import json

import requests


def fetch_bounties(after_cursor=None):
    url = "https://replit.com/graphql"
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Host": "replit.com",
        "Origin": "https://replit.com",
        "Referer": "https://replit.com/bounties?status=completed&order=creationDateDescending",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "x-client-version": "c6ef787e",
        "x-forwarded-host": "replit.com",
        "x-requested-with": "XMLHttpRequest",
    }
    query = """
    query BountiesPageSearch($input: BountySearchInput!) {
      bountySearch(input: $input) {
        ... on BountySearchConnection {
          items {
            id
            title
            descriptionPreview
            description
            cycles
            deadline
            status
            slug
            solverPayout
            timeCreated
            applicationCount
            isUnlisted
            solver {
              id
              username
              image
              url
            }
            user {
              id
              username
              image
              url
            }
          }
          pageInfo {
            hasNextPage
            nextCursor
          }
        }
      }
    }
    """
    variables = {
        "input": {
            "after": after_cursor,
            "count": 10,  # Adjust the count as needed
            "searchQuery": "",
            "statuses": ["completed"],
            "order": "creationDateDescending",
            "listingState": "listed",
        }
    }
    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    try:
        response.raise_for_status()  # Check if the response status code is 200
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")  # HTTP error

    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print("Raw response:", response.text)  # Print raw response text
    except requests.exceptions.RequestException as e:
        print(f"Request error occurred: {e}")  # Other errors

    return None


def download_bounties():
    all_bounties = []
    next_cursor = None
    try:
        while True:
            print("Fetching bounties")
            data = fetch_bounties(after_cursor=next_cursor)
            if not data:
                raise ValueError("Failed to download bounties")

            bounties = data["data"]["bountySearch"]["items"]
            all_bounties.extend(bounties)
            page_info = data["data"]["bountySearch"]["pageInfo"]
            if page_info["hasNextPage"]:
                next_cursor = page_info["nextCursor"]
            else:
                break
    except Exception as e:
        print(e)
        print("Failed to download bounties")
        return
    finally:
        # Save the data
        with open("bounties.json", "w") as file:
            json.dump(all_bounties, file, indent=4)


if __name__ == "__main__":
    with open("bounties.json", "r") as file:
        data = json.load(file)
        print(len(data))
    total = 0
    cycles_total = 0
    for bounty in data:
        total += bounty["solverPayout"]
        cycles_total += bounty["cycles"]

    print((cycles_total - total) * 0.01)

    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer

    # Extracting the 'descriptionPreview' field
    descriptions = [
        bounty["descriptionPreview"]
        for bounty in data
        if "descriptionPreview" in bounty
    ]

    # Using TF-IDF to vectorize the descriptions
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(descriptions)

    # Perform KMeans clustering with 3 clusters
    kmeans = KMeans(n_clusters=10, random_state=42)
    kmeans.fit(X)

    # Find the cluster centers
    centers = kmeans.cluster_centers_

    # Find the index of the closest point in each cluster to its center
    closest_points = []
    for i in range(3):
        center_vec = centers[i]
        distances = np.linalg.norm(X - center_vec, axis=1)
        closest_point_index = np.argmin(distances)
        closest_points.append(closest_point_index)

    # Extract the corresponding descriptions
    closest_descriptions = [descriptions[i] for i in closest_points]

    print(closest_descriptions)

    print(total * 0.01)

    # download_bounties()
