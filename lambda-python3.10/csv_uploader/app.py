import json
import boto3
import base64
import os
from datetime import datetime
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function to handle CSV file uploads to S3
    
    Expected event body: {
        "filename": "data.csv",
        "fileContent": "base64 encoded file content"
    }
    """
    
    try:
        # CORS headers for React frontend
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Content-Type": "application/json"
        }
        
        # Handle CORS preflight requests
        if event.get('httpMethod') == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"message": "CORS preflight successful"})
            }
        
        # Parse the request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        filename = body.get('filename')
        file_content = body.get('fileContent')  # base64 encoded
        
        # Validation
        if not filename or not file_content:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "error": "Missing filename or fileContent",
                    "message": "Both 'filename' and 'fileContent' are required"
                })
            }
        
        # Validate file extension
        if not filename.lower().endswith('.csv'):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "error": "Invalid file type",
                    "message": "Only CSV files are allowed"
                })
            }
        
        # Get S3 bucket from environment variable
        bucket_name = os.environ.get('S3_BUCKET')
        if not bucket_name:
            return {
                "statusCode": 500,
                "headers": headers,
                "body": json.dumps({
                    "error": "Server configuration error",
                    "message": "S3_BUCKET environment variable not set"
                })
            }
        
        # Decode the base64 file content
        try:
            decoded_content = base64.b64decode(file_content)
        except Exception as e:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "error": "Invalid file content",
                    "message": f"Failed to decode file content: {str(e)}"
                })
            }
        
        # Create a unique key with timestamp
        timestamp = datetime.now().strftime('%Y/%m/%d/%H%M%S')
        s3_key = f"csv-uploads/{timestamp}/{filename}"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=decoded_content,
            ContentType='text/csv',
            Metadata={
                'upload-timestamp': datetime.now().isoformat(),
                'original-filename': filename
            }
        )
        
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "File uploaded successfully",
                "s3_bucket": bucket_name,
                "s3_key": s3_key,
                "filename": filename
            })
        }
        
    except ClientError as e:
        print(f"AWS Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "error": "AWS Error",
                "message": f"Failed to upload file to S3: {str(e)}"
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }
