import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_publication_id():
    api_key = os.getenv("HASHNODE_API_KEY")
    
    query = """
    query {
        me {
            publications(first: 10) {
                edges {
                    node {
                        id
                        title
                    }
                }
            }
        }
    }
    """
    
    response = requests.post(
        "https://gql.hashnode.com",
        json={"query": query},
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
    )
    
    data = response.json()
    print(f"Hashnode response: {data}")
    
    edges = data["data"]["me"]["publications"]["edges"]
    if not edges:
        print("No publications found on this Hashnode account")
        return None
    
    publication_id = edges[0]["node"]["id"]
    print(f"Publication ID: {publication_id}")
    return publication_id


def publish_to_hashnode(title, content):
    api_key = os.getenv("HASHNODE_API_KEY")
    publication_id = get_publication_id()

    mutation = """
    mutation PublishPost($input: PublishPostInput!) {
        publishPost(input: $input) {
            post {
                id
                title
                url
            }
        }
    }
    """

    variables = {
        "input": {
            "title": title,
            "contentMarkdown": content,
            "publicationId": publication_id,
            "tags": []
        }
    }

    response = requests.post(
        "https://gql.hashnode.com",
        json={"query": mutation, "variables": variables},
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
    )

    data = response.json()
    
    if "errors" in data:
        print(f"Error: {data['errors']}")
        return None
    
    post_url = data["data"]["publishPost"]["post"]["url"]
    print(f"Published successfully: {post_url}")
    return post_url