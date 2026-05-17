import requests
import os
import sys
import time

BASE_URL = os.getenv("BASE_URL", "http://localhost")
SERVICES = ["auth", "product", "order", "payment", "user", "notification"]

def test_health_endpoints():
    print("Testing health endpoints...")
    for service in SERVICES:
        url = f"{BASE_URL}/api/{service}/health"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print(f"{service} service: OK")
                else:
                    print(f"{service} service: DEGRADED - {data}")
                    return False
            else:
                print(f"{service} service: FAILED (HTTP {response.status_code})")
                return False
        except Exception as e:
            print(f"{service} service: ERROR - {str(e)}")
            return False
    return True

def test_auth_login():
    print("Testing authentication...")
    url = f"{BASE_URL}/api/auth/login"
    try:
        response = requests.post(
            url,
            auth=("admin", "admin123"),
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("Authentication: OK")
                return data.get("access_token")
            else:
                print("Authentication: No token received")
                return None
        else:
            print(f"Authentication: FAILED (HTTP {response.status_code})")
            return None
    except Exception as e:
        print(f"Authentication: ERROR - {str(e)}")
        return None

def test_product_listing():
    print("Testing product listing...")
    url = f"{BASE_URL}/api/products/products"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "products" in data:
                print(f"Product listing: OK ({len(data['products'])} products)")
                return True
        print(f"Product listing: FAILED (HTTP {response.status_code})")
        return False
    except Exception as e:
        print(f"Product listing: ERROR - {str(e)}")
        return False

def test_order_creation():
    print("Testing order creation...")
    url = f"{BASE_URL}/api/orders/orders"
    order_data = {
        "user_id": "test_user",
        "items": [{"product_id": 1, "quantity": 1, "price": 29.99}],
        "total_amount": 29.99
    }
    try:
        response = requests.post(url, json=order_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "order_id" in data:
                print(f"Order creation: OK (Order ID: {data['order_id']})")
                return data.get("order_id")
        print(f"Order creation: FAILED (HTTP {response.status_code})")
        return None
    except Exception as e:
        print(f"Order creation: ERROR - {str(e)}")
        return None

def test_payment_processing():
    print("Testing payment processing...")
    url = f"{BASE_URL}/api/payment/payments"
    payment_data = {
        "order_id": 1,
        "amount": 29.99,
        "payment_method": "credit_card"
    }
    try:
        response = requests.post(url, json=payment_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") in ["completed", "failed"]:
                print(f"Payment processing: OK (Status: {data.get('status')})")
                return True
        print(f"Payment processing: FAILED (HTTP {response.status_code})")
        return False
    except Exception as e:
        print(f"Payment processing: ERROR - {str(e)}")
        return False

def test_notification_sending():
    print("Testing notification sending...")
    url = f"{BASE_URL}/api/notification/notifications/email"
    notification_data = {
        "to_email": "test@example.com",
        "subject": "Test Notification",
        "body": "This is a test"
    }
    try:
        response = requests.post(url, json=notification_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "queued":
                print("Notification sending: OK")
                return True
        print(f"Notification sending: FAILED (HTTP {response.status_code})")
        return False
    except Exception as e:
        print(f"Notification sending: ERROR - {str(e)}")
        return False

def test_database_connectivity():
    print("Testing database connectivity...")
    for service in ["auth", "product", "order", "payment", "user"]:
        url = f"{BASE_URL}/api/{service}/health"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("database") == "connected":
                    print(f"{service} database: OK")
                else:
                    print(f"{service} database: DISCONNECTED")
                    return False
        except Exception as e:
            print(f"{service} database: ERROR - {str(e)}")
            return False
    return True

def test_http_to_https_redirect():
    print("Testing HTTP to HTTPS redirect...")
    http_url = BASE_URL.replace("https://", "http://")
    try:
        response = requests.get(http_url, allow_redirects=False, timeout=10)
        if response.status_code in [301, 302]:
            location = response.headers.get("Location", "")
            if location.startswith("https://"):
                print("HTTP to HTTPS redirect: OK")
                return True
        print(f"HTTP to HTTPS redirect: FAILED (Status {response.status_code})")
        return False
    except Exception as e:
        print(f"HTTP to HTTPS redirect: ERROR - {str(e)}")
        return False

def main():
    print("=" * 50)
    print("Starting Integration Tests")
    print("=" * 50)

    time.sleep(5)

    tests = [
        ("Health Endpoints", test_health_endpoints),
        ("Database Connectivity", test_database_connectivity),
        ("HTTP to HTTPS Redirect", test_http_to_https_redirect),
        ("Product Listing", test_product_listing),
        ("Auth Login", test_auth_login),
        ("Order Creation", test_order_creation),
        ("Payment Processing", test_payment_processing),
        ("Notification Sending", test_notification_sending),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
        if test_name != "Auth Login" and result is False:
            print(f"CRITICAL: {test_name} failed")

    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        if result:
            passed += 1
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\nALL TESTS PASSED - Deployment successful")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED - Check deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()