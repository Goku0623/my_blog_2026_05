import asyncio
import httpx
import pytest


pytestmark = pytest.mark.skip(reason="manual integration script, not part of pytest suite")


BASE_URL = "http://localhost:8000/api/v1"


async def test_articles_flow():
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Articles Module\n")
        
        print("=" * 60)
        print("  Step 1: Login as Admin")
        print("=" * 60 + "\n")
        
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin123456"}
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        access_token = data["data"]["access_token"]
        print(f"✓ Login successful\n")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        print("=" * 60)
        print("  Step 2: Create Category")
        print("=" * 60 + "\n")
        
        response = await client.post(
            f"{BASE_URL}/admin/categories",
            json={
                "name": "技术分享",
                "slug": "tech",
                "description": "技术相关文章",
                "sort_order": 1
            },
            headers=headers
        )
        
        if response.status_code == 200:
            category_data = response.json()["data"]
            category_id = category_data["id"]
            print(f"✓ Category created: {category_data['name']} (ID: {category_id})\n")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}\n")
            return
        
        print("=" * 60)
        print("  Step 3: Create Tags")
        print("=" * 60 + "\n")
        
        tag_ids = []
        tags = [
            {"name": "Python", "slug": "python", "color": "#3776AB"},
            {"name": "FastAPI", "slug": "fastapi", "color": "#009688"}
        ]
        
        for tag in tags:
            response = await client.post(
                f"{BASE_URL}/admin/tags",
                json=tag,
                headers=headers
            )
            
            if response.status_code == 200:
                tag_data = response.json()["data"]
                tag_ids.append(tag_data["id"])
                print(f"✓ Tag created: {tag_data['name']} (ID: {tag_data['id']})")
            else:
                print(f"❌ Failed: {response.status_code}")
        
        print()
        
        print("=" * 60)
        print("  Step 4: Create Article (Draft)")
        print("=" * 60 + "\n")
        
        article_data = {
            "title": "FastAPI 快速入门指南",
            "summary": "学习如何使用 FastAPI 构建高性能的 Web API",
            "content": """
# FastAPI 快速入门

FastAPI 是一个现代化、快速的 Python Web 框架。

## 特性

- 高性能
- 自动生成文档
- 类型提示支持

## 安装

```bash
pip install fastapi uvicorn
```

## 示例

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```
            """,
            "category_id": category_id,
            "tag_ids": tag_ids,
            "status": "draft",
            "cover_image": "https://example.com/cover.jpg",
            "allow_comment": True,
            "seo_title": "FastAPI 快速入门 - 完整指南",
            "seo_description": "详细的 FastAPI 入门教程",
            "seo_keywords": "FastAPI, Python, Web API"
        }
        
        response = await client.post(
            f"{BASE_URL}/admin/articles",
            json=article_data,
            headers=headers
        )
        
        if response.status_code == 200:
            article = response.json()["data"]
            article_id = article["id"]
            article_slug = article["slug"]
            print(f"✓ Article created:")
            print(f"  - ID: {article_id}")
            print(f"  - Title: {article['title']}")
            print(f"  - Slug: {article_slug}")
            print(f"  - Status: {article['status']}\n")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}\n")
            return
        
        print("=" * 60)
        print("  Step 5: Publish Article")
        print("=" * 60 + "\n")
        
        response = await client.post(
            f"{BASE_URL}/admin/articles/{article_id}/publish",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✓ Article published successfully\n")
        else:
            print(f"❌ Failed: {response.status_code}\n")
        
        print("=" * 60)
        print("  Step 6: Get Public Article List")
        print("=" * 60 + "\n")
        
        response = await client.get(f"{BASE_URL}/articles?page=1&page_size=10")
        
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"✓ Found {data['total']} article(s)")
            print(f"  - Page: {data['page']}/{data['total_pages']}")
            print(f"  - Items on this page: {len(data['items'])}\n")
        else:
            print(f"❌ Failed: {response.status_code}\n")
        
        print("=" * 60)
        print("  Step 7: Get Article Detail (Public)")
        print("=" * 60 + "\n")
        
        response = await client.get(f"{BASE_URL}/articles/{article_slug}")
        
        if response.status_code == 200:
            article = response.json()["data"]
            print(f"✓ Article details retrieved:")
            print(f"  - Title: {article['title']}")
            print(f"  - Views: {article['view_count']}")
            print(f"  - Category: {article['category']['name'] if article['category'] else 'None'}")
            print(f"  - Tags: {', '.join([t['name'] for t in article['tags']])}\n")
        else:
            print(f"❌ Failed: {response.status_code}\n")
        
        print("=" * 60)
        print("  Step 8: Search Articles")
        print("=" * 60 + "\n")
        
        response = await client.get(f"{BASE_URL}/articles/search?keyword=FastAPI&page=1&page_size=10")
        
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"✓ Search results: {data['total']} article(s) found\n")
        else:
            print(f"❌ Failed: {response.status_code}\n")
        
        print("=" * 60)
        print("  Step 9: Update Article")
        print("=" * 60 + "\n")
        
        response = await client.put(
            f"{BASE_URL}/admin/articles/{article_id}",
            json={"summary": "更新后的摘要 - FastAPI 完整教程"},
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✓ Article updated successfully\n")
        else:
            print(f"❌ Failed: {response.status_code}\n")
        
        print("=" * 60)
        print("  Step 10: List Categories")
        print("=" * 60 + "\n")
        
        response = await client.get(f"{BASE_URL}/categories")
        
        if response.status_code == 200:
            categories = response.json()["data"]
            print(f"✓ Found {len(categories)} category(ies):")
            for cat in categories:
                print(f"  - {cat['name']} ({cat['slug']})")
            print()
        else:
            print(f"❌ Failed: {response.status_code}\n")
        
        print("=" * 60)
        print("  Step 11: List Tags")
        print("=" * 60 + "\n")
        
        response = await client.get(f"{BASE_URL}/tags")
        
        if response.status_code == 200:
            tags = response.json()["data"]
            print(f"✓ Found {len(tags)} tag(s):")
            for tag in tags:
                print(f"  - {tag['name']} ({tag['slug']})")
            print()
        else:
            print(f"❌ Failed: {response.status_code}\n")
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Articles Module Test Suite")
    print("=" * 60 + "\n")
    print("⚠️  Prerequisites:")
    print("  1. Backend server running on http://localhost:8000")
    print("  2. Admin user created (username: admin, password: admin123456)")
    print("  3. PostgreSQL and Redis running\n")
    
    try:
        asyncio.run(test_articles_flow())
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
