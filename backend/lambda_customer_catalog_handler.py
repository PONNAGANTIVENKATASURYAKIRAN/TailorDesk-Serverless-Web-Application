import json
import boto3
import uuid
from decimal import Decimal
from datetime import datetime
from botocore.config import Config

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns", region_name="us-east-1")
s3_client = boto3.client(
    "s3", region_name="us-east-1", config=Config(signature_version="s3v4")
)

BUCKET_NAME = "tailordesk-portal-surya"

catalog_table = dynamodb.Table("TailorCatalog")
customer_table = dynamodb.Table("TailorCustomers")
feedback_table = dynamodb.Table("TailorFeedback")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def send_customer_sms(phone, message):
    try:
        clean_phone = phone.strip().replace(" ", "").replace("-", "")
        if not clean_phone.startswith("+"):
            if clean_phone.startswith("91") and len(clean_phone) == 12:
                clean_phone = f"+{clean_phone}"
            elif len(clean_phone) == 10:
                clean_phone = f"+91{clean_phone}"

        sns.publish(
            PhoneNumber=clean_phone,
            Message=message,
            MessageAttributes={
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                }
            },
        )
        print(f"SMS successfully sent to {clean_phone}")
    except Exception as e:
        print(f"SMS Dispatch Failed: {str(e)}")


def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET,DELETE",
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    path = event.get("path", "")
    method = event.get("httpMethod")

    # PRESIGNED UPLOAD ROUTE WITH CATEGORY FOLDER SEPARATION
    if "/catalog/upload-url" in path and method == "POST":
        body = json.loads(event.get("body", "{}"))
        filename = body.get("filename", f"{uuid.uuid4().hex[:8]}.jpg")
        content_type = body.get("contentType", "image/jpeg")
        category = body.get("category", "Dresses")

        # Route to dedicated S3 folder
        if category == "Maggam":
            folder = "Maggam_Images"
        else:
            folder = "Dresses_Images"

        clean_filename = f"catalog-{uuid.uuid4().hex[:6]}-{filename.replace(' ', '_')}"
        s3_key = f"{folder}/{clean_filename}"

        upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=300,
        )

        final_image_url = f"https://d34hvud16ku84i.cloudfront.net/{s3_key}"

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"uploadUrl": upload_url, "imageUrl": final_image_url}),
        }

    # CATALOG ROUTES
    if "/catalog" in path:
        if method == "GET":
            items = catalog_table.scan().get("Items", [])
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(items, cls=DecimalEncoder),
            }
        elif method == "POST":
            body = json.loads(event.get("body", "{}"))
            item = {
                "category": body.get("category"),
                "modelId": str(uuid.uuid4())[:8],
                "nameEn": body.get("nameEn"),
                "nameTe": body.get("nameTe"),
                "price": Decimal(str(body.get("price", 0))),
                "imageUrl": body.get("imageUrl"),
            }
            catalog_table.put_item(Item=item)
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(item, cls=DecimalEncoder),
            }
        elif method == "DELETE":
            body = json.loads(event.get("body", "{}"))
            catalog_table.delete_item(
                Key={"category": body.get("category"), "modelId": body.get("modelId")}
            )
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"message": "Catalog item deleted"}),
            }

    # FEEDBACK ROUTES
    if "/feedback" in path:
        if method == "GET":
            items = feedback_table.scan().get("Items", [])
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(items, cls=DecimalEncoder),
            }
        elif method == "POST":
            body = json.loads(event.get("body", "{}"))
            item = {
                "feedbackId": str(uuid.uuid4())[:8],
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "name": body.get("name", "Anonymous"),
                "phone": body.get("phone", "N/A"),
                "rating": Decimal(str(body.get("rating", 5))),
                "message": body.get("message", ""),
            }
            feedback_table.put_item(Item=item)
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(item, cls=DecimalEncoder),
            }
        elif method == "DELETE":
            body = json.loads(event.get("body", "{}"))
            feedback_table.delete_item(Key={"feedbackId": body.get("feedbackId")})
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"message": "Feedback deleted"}),
            }

    # CUSTOMER ROUTES
    if "/customers" in path:
        if method == "GET":
            items = customer_table.scan().get("Items", [])
            deduped = {}
            for item in items:
                phone = item.get("phone")
                if phone not in deduped or item.get("timestamp", "") > deduped[
                    phone
                ].get("timestamp", ""):
                    deduped[phone] = item
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(list(deduped.values()), cls=DecimalEncoder),
            }

        elif method == "POST":
            body = json.loads(event.get("body", "{}"))
            phone = body.get("phone")
            name = body.get("name", "Customer")
            status = body.get("status", "3. Just Browsed")
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            existing = customer_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("phone").eq(phone)
            ).get("Items", [])
            for old in existing:
                customer_table.delete_item(
                    Key={"phone": phone, "timestamp": old["timestamp"]}
                )

            item = {
                "phone": phone,
                "timestamp": timestamp,
                "name": name,
                "address": body.get("address"),
                "status": status,
                "services": body.get("services", []),
                "itemsDetail": body.get("itemsDetail", []),
                "instructions": body.get("instructions", ""),
            }
            customer_table.put_item(Item=item)

            if "1. Selected & Reached" in status or "Stitching" in status:
                sms_text = f"Namaste {name}, your order has been received at Lakshmi Devi Ladies Tailors. We will reach out shortly for fitting confirmation. Call: 8008717360."
                send_customer_sms(phone, sms_text)
            elif "2. Selected but Not Now" in status:
                sms_text = f"Namaste {name}, thank you for contacting Lakshmi Devi Ladies Tailors. Smt. Lakshmi Devi will call you back soon for details. Call: 8008717360."
                send_customer_sms(phone, sms_text)

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(item, cls=DecimalEncoder),
            }

        elif method == "DELETE":
            body = json.loads(event.get("body", "{}"))
            customer_table.delete_item(
                Key={"phone": body.get("phone"), "timestamp": body.get("timestamp")}
            )
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"message": "Customer deleted"}),
            }

    return {
        "statusCode": 404,
        "headers": headers,
        "body": json.dumps({"error": "Not Found"}),
    }
