"""
AWS CDK Stack for Multi-Agent System Infrastructure
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_events as events,
    aws_events_targets as targets,
    RemovalPolicy
)
from constructs import Construct


class MultiAgentStack(Stack):
    """
    Infrastructure for ABSolution Multi-Agent AI System
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Tables
        self.create_dynamodb_tables()

        # Lambda Functions
        self.create_lambda_functions()

        # API Gateway
        self.create_api_gateway()

        # Step Functions Workflow
        self.create_orchestration_workflow()

        # Event Rules
        self.create_event_rules()

    def create_dynamodb_tables(self):
        """Create DynamoDB tables for conversation and session management."""

        # Conversation history table
        self.conversation_table = dynamodb.Table(
            self, "ConversationTable",
            table_name="abs-agent-conversations",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True
        )

        # Session management table
        self.session_table = dynamodb.Table(
            self, "SessionTable",
            table_name="abs-agent-sessions",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            time_to_live_attribute="ttl"
        )

    def create_lambda_functions(self):
        """Create Lambda functions for agent coordination."""

        # IAM role for Lambda with Bedrock access
        lambda_role = iam.Role(
            self, "AgentLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Add Bedrock permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            resources=["*"]
        ))

        # Add SageMaker permissions
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "sagemaker:InvokeEndpoint"
            ],
            resources=["*"]
        ))

        # Grant DynamoDB access
        self.conversation_table.grant_read_write_data(lambda_role)
        self.session_table.grant_read_write_data(lambda_role)

        # Agent Coordinator Lambda
        self.coordinator_lambda = lambda_.Function(
            self, "AgentCoordinator",
            function_name="abs-agent-coordinator",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="agent_coordinator.lambda_handler",
            code=lambda_.Code.from_asset("../src/agents"),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment={
                "CONVERSATION_TABLE": self.conversation_table.table_name,
                "SESSION_TABLE": self.session_table.table_name,
                "SAGEMAKER_RISK_ENDPOINT": "abs-risk-scoring-model"
            }
        )

        # Dialogue Panel REST API Lambda
        self.dialogue_rest_lambda = lambda_.Function(
            self, "DialogueRestAPI",
            function_name="abs-dialogue-rest-api",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="dialogue_panel.rest_api_handler",
            code=lambda_.Code.from_asset("../src/agents"),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=512,
            environment={
                "CONVERSATION_TABLE": self.conversation_table.table_name,
                "SESSION_TABLE": self.session_table.table_name
            }
        )

        # Individual Agent Lambdas (for parallel execution)
        self.data_analyst_lambda = self._create_agent_lambda(
            "DataAnalyst", lambda_role, "data_analyst"
        )
        self.risk_assessor_lambda = self._create_agent_lambda(
            "RiskAssessor", lambda_role, "risk_assessor"
        )
        self.report_generator_lambda = self._create_agent_lambda(
            "ReportGenerator", lambda_role, "report_generator"
        )
        self.benchmark_analyst_lambda = self._create_agent_lambda(
            "BenchmarkAnalyst", lambda_role, "benchmark_analyst"
        )
        self.alert_monitor_lambda = self._create_agent_lambda(
            "AlertMonitor", lambda_role, "alert_monitor"
        )

    def _create_agent_lambda(
        self,
        agent_name: str,
        role: iam.Role,
        agent_type: str
    ) -> lambda_.Function:
        """Helper to create individual agent Lambda functions."""
        return lambda_.Function(
            self, f"{agent_name}Lambda",
            function_name=f"abs-agent-{agent_type}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="agent_coordinator.lambda_handler",
            code=lambda_.Code.from_asset("../src/agents"),
            role=role,
            timeout=Duration.seconds(180),
            memory_size=512,
            environment={
                "AGENT_TYPE": agent_type,
                "CONVERSATION_TABLE": self.conversation_table.table_name
            }
        )

    def create_api_gateway(self):
        """Create API Gateway for dialogue panel."""

        # REST API
        self.api = apigateway.RestApi(
            self, "DialogueAPI",
            rest_api_name="ABSolution Dialogue API",
            description="Multi-agent dialogue interface for ABS analysis",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS
            )
        )

        # Integrate with Lambda
        dialogue_integration = apigateway.LambdaIntegration(
            self.dialogue_rest_lambda
        )

        # API Resources
        # POST /session - Create new session
        session_resource = self.api.root.add_resource("session")
        session_resource.add_method("POST", dialogue_integration)

        # POST /message - Send message
        message_resource = self.api.root.add_resource("message")
        message_resource.add_method("POST", dialogue_integration)

        # GET /history/{session_id} - Get history
        history_resource = self.api.root.add_resource("history")
        history_id_resource = history_resource.add_resource("{session_id}")
        history_id_resource.add_method("GET", dialogue_integration)

        # POST /export - Export conversation
        export_resource = self.api.root.add_resource("export")
        export_resource.add_method("POST", dialogue_integration)

    def create_orchestration_workflow(self):
        """Create Step Functions workflow for complex multi-agent orchestration."""

        # Define individual agent tasks
        data_analyst_task = tasks.LambdaInvoke(
            self, "InvokeDataAnalyst",
            lambda_function=self.data_analyst_lambda,
            payload=sfn.TaskInput.from_object({
                "agent": "data_analyst",
                "task.$": "$.task",
                "context.$": "$.context"
            }),
            result_path="$.data_analyst_result"
        )

        risk_assessor_task = tasks.LambdaInvoke(
            self, "InvokeRiskAssessor",
            lambda_function=self.risk_assessor_lambda,
            payload=sfn.TaskInput.from_object({
                "agent": "risk_assessor",
                "task.$": "$.task",
                "context.$": "$.context"
            }),
            result_path="$.risk_assessor_result"
        )

        report_generator_task = tasks.LambdaInvoke(
            self, "InvokeReportGenerator",
            lambda_function=self.report_generator_lambda,
            payload=sfn.TaskInput.from_object({
                "agent": "report_generator",
                "task.$": "$.task",
                "context.$": "$.context"
            }),
            result_path="$.report_generator_result"
        )

        # Parallel execution for supporting agents
        parallel_agents = sfn.Parallel(
            self, "ParallelAgentExecution",
            result_path="$.parallel_results"
        )
        parallel_agents.branch(data_analyst_task)
        parallel_agents.branch(risk_assessor_task)

        # Sequential workflow: parallel agents -> report generation
        definition = parallel_agents.next(report_generator_task)

        # Create state machine
        self.workflow = sfn.StateMachine(
            self, "MultiAgentWorkflow",
            state_machine_name="abs-multi-agent-workflow",
            definition=definition,
            timeout=Duration.minutes(15)
        )

    def create_event_rules(self):
        """Create EventBridge rules for automated agent triggers."""

        # Daily market summary rule
        daily_rule = events.Rule(
            self, "DailyMarketSummary",
            schedule=events.Schedule.cron(hour="8", minute="0"),
            description="Trigger daily ABS market summary generation"
        )
        daily_rule.add_target(
            targets.LambdaFunction(self.report_generator_lambda)
        )

        # Alert monitoring rule (every 15 minutes)
        alert_rule = events.Rule(
            self, "AlertMonitoring",
            schedule=events.Schedule.rate(Duration.minutes(15)),
            description="Monitor for ABS alerts and anomalies"
        )
        alert_rule.add_target(
            targets.LambdaFunction(self.alert_monitor_lambda)
        )
