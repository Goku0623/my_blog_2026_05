import asyncio
import httpx
import pytest


pytestmark = pytest.mark.skip(reason="manual integration script, not part of pytest suite")


BASE_URL = "http://localhost:8000/api/v1"


async def test_auth_flow():
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Authentication Flow\n")
        
        print("1️⃣ Testing Login...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={
                    "username": "admin",
                    "password": "admin123456"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data["data"]["access_token"]
                refresh_token = data["data"]["refresh_token"]
                print(f"   ✓ Login successful")
                print(f"   - Access Token: {access_token[:50]}...")
                print(f"   - Refresh Token: {refresh_token[:50]}...")
                print(f"   - Expires in: {data['data']['expires_in']}s\n")
            else:
                print(f"   ✗ Login failed: {response.status_code}")
                print(f"   Response: {response.text}\n")
                return
        except Exception as e:
            print(f"   ✗ Error: {e}\n")
            return
        
        print("2️⃣ Testing Get Current User...")
        try:
            response = await client.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                user = data["data"]
                print(f"   ✓ User info retrieved")
                print(f"   - ID: {user['id']}")
                print(f"   - Username: {user['username']}")
                print(f"   - Email: {user['email']}")
                print(f"   - Is Active: {user['is_active']}\n")
            else:
                print(f"   ✗ Failed: {response.status_code}")
                print(f"   Response: {response.text}\n")
        except Exception as e:
            print(f"   ✗ Error: {e}\n")
        
        print("3️⃣ Testing Token Refresh...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                new_access_token = data["data"]["access_token"]
                print(f"   ✓ Token refreshed")
                print(f"   - New Access Token: {new_access_token[:50]}...\n")
            else:
                print(f"   ✗ Failed: {response.status_code}")
                print(f"   Response: {response.text}\n")
        except Exception as e:
            print(f"   ✗ Error: {e}\n")
        
        print("4️⃣ Testing Logout...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                print(f"   ✓ Logout successful\n")
            else:
                print(f"   ✗ Failed: {response.status_code}")
                print(f"   Response: {response.text}\n")
        except Exception as e:
            print(f"   ✗ Error: {e}\n")
        
        print("5️⃣ Testing Access After Logout (should fail)...")
        try:
            response = await client.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 401:
                print(f"   ✓ Access denied as expected\n")
            else:
                print(f"   ✗ Unexpected: {response.status_code}")
                print(f"   Response: {response.text}\n")
        except Exception as e:
            print(f"   ✗ Error: {e}\n")
        
        print("✅ Authentication flow test completed!")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Auth Module Test Suite")
    print("="*60 + "\n")
    print("⚠️  Make sure the backend server is running on http://localhost:8000")
    print("⚠️  Run: uv run uvicorn app.main:app --reload\n")
    
    try:
        asyncio.run(test_auth_flow())
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
