# AWS Lambda CSV to S3 Uploader

This project demonstrates a complete solution for uploading CSV files from a React frontend to AWS S3 via a Lambda function and API Gateway.

## Architecture

```
React Frontend (CSVUploader.jsx)
    ↓
API Gateway (POST /upload-csv)
    ↓
Lambda Function (csv_uploader/app.py)
    ↓
S3 Bucket (csv-storage-{accountid}-{region})
```

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.10+
- Node.js and npm (for React development)
- SAM CLI (for deployment)
- Git

## Project Structure

```
lambda-python3.10/
├── csv_uploader/              # New Lambda function for CSV uploads
│   ├── app.py                 # Lambda handler
│   ├── requirements.txt        # Python dependencies
│   └── __init__.py
├── hello_world/               # Existing Lambda function
│   ├── app.py
│   ├── requirements.txt
│   └── __init__.py
├── frontend/                  # React frontend example
│   └── CSVUploader.jsx        # React component
├── tests/                     # Test files
├── template.yaml              # SAM template
└── samconfig.toml            # SAM configuration
```

## Features

✅ **CSV File Upload** - Upload CSV files via React frontend  
✅ **Base64 Encoding** - Secure file transmission  
✅ **CORS Support** - Works with any React frontend origin  
✅ **S3 Integration** - Files stored with timestamp organization  
✅ **Error Handling** - Comprehensive validation and error messages  
✅ **File Versioning** - S3 versioning enabled on storage bucket  
✅ **Security** - S3 bucket with public access blocked  

## Deployment

### 1. Build the SAM Template

```bash
cd lambda-python3.10
sam build
```

### 2. Deploy to AWS

First time deployment (guided):
```bash
sam deploy --guided
```

The guided deployment will ask for:
- Stack Name: `csv-uploader-stack`
- AWS Region: Choose your region
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save parameters: `Y`

Subsequent deployments:
```bash
sam deploy
```

### 3. Get the API Endpoint

After deployment, SAM will output the API endpoint. Look for:
```
CSVUploaderApi: https://xxxxx.execute-api.{region}.amazonaws.com/Prod/upload-csv
```

## Usage in React

### 1. Install the Component

Copy `frontend/CSVUploader.jsx` to your React project:

```bash
cp frontend/CSVUploader.jsx src/components/
```

### 2. Use in Your App

```jsx
import CSVUploader from './components/CSVUploader';

function App() {
  const apiEndpoint = 'https://your-api-endpoint/upload-csv';

  return (
    <div className="App">
      <CSVUploader apiEndpoint={apiEndpoint} />
    </div>
  );
}

export default App;
```

### 3. API Request Format

The component sends requests in this format:

```json
{
  "filename": "data.csv",
  "fileContent": "base64-encoded-content"
}
```

### 4. API Response Format

Success (200):
```json
{
  "message": "File uploaded successfully",
  "s3_bucket": "csv-storage-xxxx-region",
  "s3_key": "csv-uploads/2024/01/15/120530/data.csv",
  "filename": "data.csv"
}
```

Error (4xx/5xx):
```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

## Timeout Configuration

The Lambda function has a **30-second timeout** to accommodate larger CSV files. Adjust in `template.yaml` if needed:

```yaml
Globals:
  Function:
    Timeout: 30  # Increase for larger files
```

## File Organization in S3

Files are organized by upload timestamp:
```
csv-uploads/
├── 2024/01/15/
│   ├── 091530/data1.csv
│   ├── 101245/data2.csv
│   └── 120530/data3.csv
```

## Testing

### 1. Test via AWS Console

Use the API Gateway test feature:
1. Go to API Gateway → your API → POST /upload-csv
2. Click "Test"
3. Use the example payload below

### 2. Test via CLI

```bash
# First, create a test CSV file
echo "name,age,city\nJohn,30,NYC\nJane,25,LA" > test.csv

# Encode to base64
base64 -w 0 test.csv > test.csv.b64
BASE64_CONTENT=$(cat test.csv.b64)

# Make the request
curl -X POST https://your-api-endpoint/upload-csv \
  -H "Content-Type: application/json" \
  -d "{\"filename\":\"test.csv\",\"fileContent\":\"$BASE64_CONTENT\"}"
```

### 3. Run Unit Tests

```bash
cd tests/unit
python -m pytest test_handler.py -v
```

## Troubleshooting

### CORS Errors in React

If you see CORS errors in your browser console:
1. Verify the API endpoint is correct
2. Ensure OPTIONS method is allowed (it is by default)
3. Check the Lambda is returning CORS headers

### File Upload Fails

Check the following:
1. File is a valid CSV (ends with `.csv`)
2. Lambda has S3 permissions (check IAM role)
3. S3 bucket exists and Lambda can access it
4. File size is reasonable (< Lambda payload limit)

### Lambda Timeout

If uploads fail with timeout:
1. Check file size
2. Increase Lambda timeout in `template.yaml`
3. Monitor CloudWatch logs for errors

## Environment Variables

The Lambda function uses:
- `S3_BUCKET` - Automatically set by SAM template

## Security Considerations

1. **File Validation** - Only `.csv` files allowed
2. **File Size** - Lambda payload limit is 6 MB for synchronous invocations
3. **S3 Permissions** - Bucket is private; only Lambda can write
4. **Encryption** - Add KMS encryption in production
5. **CORS** - Set specific origins in production instead of `*`

```yaml
# In template.yaml, modify CORS policy for production
ApiDomain:
  Type: AWS::Apigateway::DomainName
  Properties:
    CorsConfiguration:
      AllowedOrigins:
        - https://yourdomain.com
```

## Advanced Customization

### 1. Add CSV Validation

Modify `csv_uploader/app.py`:
```python
import csv
from io import StringIO

# Validate CSV format
def validate_csv(content):
    try:
        csv.DictReader(StringIO(content.decode('utf-8')))
        return True
    except Exception:
        return False
```

### 2. Add AWS CloudWatch Logging

```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info(f"Uploaded file: {filename}")
```

### 3. Add Lambda Layer for Dependencies

Store shared dependencies in a Lambda Layer to reduce deployment size.

## GitHub Integration

### 1. Initial Setup

```bash
git init
git add .
git commit -m "Initial commit: AWS Lambda CSV uploader with React frontend"
```

### 2. Push to GitHub

```bash
git remote add origin https://github.com/your-username/aws.git
git branch -M main
git push -u origin main
```

### 3. Use with GitHub Copilot

Use GitHub Copilot in VS Code to:
- Generate test cases for Lambda functions
- Create additional React components
- Write CloudFormation/SAM templates
- Generate documentation

**Tips for using Copilot:**
- Type detailed comments for better suggestions
- Reference existing code patterns
- Use `//` or `#` comments to guide code generation

## Next Steps

1. ✅ Deploy the Lambda function
2. ✅ Test the API endpoint
3. ✅ Integrate React component in your app
4. ✅ Monitor CloudWatch logs
5. ⬜ Add additional validation
6. ⬜ Set up CI/CD pipeline
7. ⬜ Add authentication (API keys/OAuth)
8. ⬜ Implement file processing workflows

## Resources

- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [S3 API Reference](https://docs.aws.amazon.com/s3/latest/dev/)
- [API Gateway CORS](https://docs.aws.amazon.com/apigateway/latest/developerguide/)
- [React File Upload](https://react.dev/)

## License

MIT License - Feel free to use this as a template for your projects.

## Support

For issues or questions:
1. Check CloudWatch logs in AWS Console
2. Review error messages in API response
3. Consult this README troubleshooting section
4. Submit issues on GitHub
