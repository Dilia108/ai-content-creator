import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_access_token():
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    
    response = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    })
    
    return response.json().get("access_token")


def get_user_id(access_token):
    response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response.json().get("sub")


def publish_to_linkedin(content):
    access_token = get_access_token()
    if not access_token:
        print("Error: Could not get LinkedIn access token")
        return None

    user_id = get_user_id(access_token)
    if not user_id:
        print("Error: Could not get LinkedIn user ID")
        return None

    post_data = {
        "author": f"urn:li:person:{user_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content[:3000]
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        },
        json=post_data
    )

    if response.status_code == 201:
        print("Published successfully to LinkedIn")
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None