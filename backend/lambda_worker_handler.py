import json
import boto3
import uuid
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("TailorWorkerLedger")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET,DELETE",
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    method = event.get("httpMethod")

    if method == "POST":
        body = json.loads(event.get("body", "{}"))
        action = body.get("action", "add_log")

        # 1. Reset pending payout for a specific worker
        if action == "settle_worker":
            worker_name = body.get("workerName")
            resp = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("workerName").eq(
                    worker_name
                )
            )
            for item in resp.get("Items", []):
                if item.get("status") == "UNPAID" and item.get("type") == "WORK_ENTRY":
                    table.update_item(
                        Key={"workerName": worker_name, "logId": item["logId"]},
                        UpdateExpression="SET #s = :paid",
                        ExpressionAttributeNames={"#s": "status"},
                        ExpressionAttributeValues={":paid": "PAID"},
                    )
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"message": "Worker settled"}),
            }

        # 2. Add Worker Profile
        if action == "create_worker":
            worker_name = body.get("workerName")
            table.put_item(
                Item={"workerName": worker_name, "logId": "PROFILE", "type": "PROFILE"}
            )
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"message": "Worker created"}),
            }

        # 3. Regular Daily Work Log with Profit Calculation
        worker_name = body.get("workerName", "Self (Smt. Lakshmi Devi)")
        pieces = Decimal(str(body.get("pieces", 1)))
        piece_rate = Decimal(str(body.get("pieceRate", 0)))
        actual_price = Decimal(str(body.get("actualPrice", 0)))

        total_worker_pay = pieces * piece_rate
        total_revenue = pieces * actual_price
        shop_profit = total_revenue - total_worker_pay

        item = {
            "workerName": worker_name,
            "logId": f"LOG#{body.get('date')}#{str(uuid.uuid4())[:8]}",
            "type": "WORK_ENTRY",
            "date": body.get("date"),
            "garment": body.get("garment", "Lining Blouse"),
            "pieces": pieces,
            "pieceRate": piece_rate,
            "actualPrice": actual_price,
            "totalWorkerPay": total_worker_pay,
            "totalRevenue": total_revenue,
            "profit": shop_profit,
            "status": body.get("status", "UNPAID"),
        }
        table.put_item(Item=item)
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(item, cls=DecimalEncoder),
        }

    if method == "GET":
        items = table.scan().get("Items", [])
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(items, cls=DecimalEncoder),
        }

    # Delete any single work entry or profile
    if method == "DELETE":
        body = json.loads(event.get("body", "{}"))
        table.delete_item(
            Key={"workerName": body.get("workerName"), "logId": body.get("logId")}
        )
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "Deleted"}),
        }

    return {
        "statusCode": 400,
        "headers": headers,
        "body": json.dumps({"error": "Unsupported"}),
    }
