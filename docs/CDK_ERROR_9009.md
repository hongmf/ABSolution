# CDK Error 9009 - Troubleshooting Guide

## Problem

When running `cdk synth` or `cdk deploy`, you see:
```
Subprocess exited with error 9009
```

## Cause

Error 9009 means "command not found". This happens when:
1. **Python executable not found**: CDK is looking for `python3` but your system uses `python`
2. **Missing dependencies**: Required Python packages not installed
3. **PATH issues**: Python not in system PATH

## Solutions

### Solution 1: Update cdk.json (Recommended)

The cdk.json has been updated to use `python` instead of `python3`:

```json
{
  "app": "python app.py"
}
```

This should work on both Windows and Linux.

### Solution 2: Use Python Directly

Instead of using CDK commands, run Python directly:

```bash
# Generate CloudFormation template
python app.py > template.json

# Or just verify it works
python app.py
```

### Solution 3: Create Python Alias (Windows)

If you have `python` but CDK expects `python3`:

**Option A: Create batch file**
Create `python3.bat` in a directory in your PATH:
```batch
@echo off
python %*
```

**Option B: Create symbolic link** (requires admin)
```cmd
mklink C:\Windows\python3.exe C:\Python311\python.exe
```

### Solution 4: Use Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Now CDK should work
cdk synth
```

### Solution 5: Check Python Installation

Verify Python is installed correctly:

```bash
# Check Python
python --version
# or
python3 --version

# Check pip
pip --version
# or
pip3 --version

# Check if Python is in PATH
where python    # Windows
which python    # Linux/Mac
```

If Python is not found, reinstall from [python.org](https://www.python.org/downloads/)

### Solution 6: Verify Dependencies

Make sure all dependencies are installed:

```bash
cd infrastructure
pip install -r requirements.txt
```

Required packages:
- aws-cdk-lib>=2.110.0
- constructs>=10.3.0
- boto3>=1.34.0

### Solution 7: Use Alternative App Command

Update `cdk.json` to use different commands:

**For Windows:**
```json
{
  "app": "cmd /c python app.py"
}
```

**For PowerShell:**
```json
{
  "app": "powershell python app.py"
}
```

**Using batch file:**
```json
{
  "app": "cdk.bat"
}
```

**Using shell script (Linux/Mac):**
```json
{
  "app": "./cdk.sh"
}
```

We've included both `cdk.bat` (Windows) and `cdk.sh` (Linux/Mac) that automatically detect and use the correct Python executable.

## Testing the Fix

After applying a solution, test it:

```bash
cd infrastructure

# Test 1: Run app.py directly
python app.py

# Test 2: CDK synth (should show CloudFormation template)
cdk synth ABSolutionMultiAgentStack

# Test 3: Check if warnings only (warnings are OK)
# You should see output, not errors
```

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'aws_cdk'"

**Solution:**
```bash
pip install aws-cdk-lib constructs
```

### Issue: "ImportError: No module named 'multi_agent_stack'"

**Solution:**
```bash
# Make sure you're in the infrastructure directory
cd infrastructure
python app.py
```

### Issue: "boto3 not found"

**Solution:**
```bash
pip install boto3
```

### Issue: Python not in PATH

**Windows:**
1. Search for "Environment Variables"
2. Edit PATH
3. Add Python directory (e.g., `C:\Python311\`)
4. Add Scripts directory (e.g., `C:\Python311\Scripts\`)
5. Restart terminal

**Linux/Mac:**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="/usr/local/bin/python3:$PATH"
```

## Platform-Specific Solutions

### Windows

1. Use the provided `cdk.bat`:
   ```json
   {
     "app": "cdk.bat"
   }
   ```

2. Or install Python launcher:
   ```json
   {
     "app": "py app.py"
   }
   ```

### Linux/Mac

1. Use the provided `cdk.sh`:
   ```json
   {
     "app": "./cdk.sh"
   }
   ```

2. Or ensure python3 is available:
   ```bash
   sudo ln -s /usr/bin/python3 /usr/local/bin/python
   ```

## Verification

Once fixed, you should see CloudFormation output:

```bash
cdk synth ABSolutionMultiAgentStack
```

Expected output:
```yaml
Resources:
  ConversationTable...:
    Type: AWS::DynamoDB::Table
    ...
  AgentCoordinator...:
    Type: AWS::Lambda::Function
    ...
```

## Still Not Working?

If none of the solutions work:

1. **Check CDK installation:**
   ```bash
   cdk --version
   npm list -g aws-cdk
   ```

2. **Reinstall CDK:**
   ```bash
   npm uninstall -g aws-cdk
   npm install -g aws-cdk
   ```

3. **Try using Docker** (nuclear option):
   ```bash
   docker run -v $(pwd):/app -w /app amazon/aws-cli:latest \
     bash -c "pip install -r requirements.txt && python app.py"
   ```

4. **Manual deployment:**
   Instead of using CDK, manually create the CloudFormation template:
   ```bash
   python app.py > template.yaml
   aws cloudformation deploy \
     --template-file template.yaml \
     --stack-name ABSolutionMultiAgentStack
   ```

## Need More Help?

- Check Python version: `python --version` (should be 3.8+)
- Check CDK version: `cdk --version` (should be 2.110.0+)
- Check Node.js version: `node --version` (should be 14+)
- Review CloudWatch logs after deployment issues
- Check AWS credentials: `aws sts get-caller-identity`
