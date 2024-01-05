from openai import OpenAI

client = OpenAI(api_key="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")
import json

import numpy as np
from sklearn.cluster import KMeans

# Set your OpenAI API key


# Function to get embeddings from OpenAI
def get_openai_embeddings(texts):
    embeddings = []
    for text in texts:
        response = client.embeddings.create(
            input=[text], model="text-embedding-ada-002"
        )
        embeddings.append(response.data[0].embedding)
    return embeddings


# Load your JSON file with descriptions
file_path = "bounties.json"  # Replace with your JSON file path
with open(file_path, "r") as file:
    bounties_data = json.load(file)

# Extracting 'descriptionPreview' fields
descriptions = [
    bounty["descriptionPreview"]
    for bounty in bounties_data
    if "descriptionPreview" in bounty
]
full_desc = [
    bounty["description"] for bounty in bounties_data if "description" in bounty
]
# # Get OpenAI embeddings
# embeddings = get_openai_embeddings(descriptions)

# with open('embeddings.json', 'w') as file:
#     json.dump(embeddings, file, indent=4)
with open("embeddings.json", "r") as file:
    embeddings = json.load(file)

# Perform KMeans clustering
kmeans = KMeans(n_clusters=10, random_state=42)
kmeans.fit(embeddings)


# Get cluster labels and count the number of occurrences of each value
unique, counts = np.unique(kmeans.labels_, return_counts=True)
cluster_sizes = dict(zip(unique, counts))

# Finding the closest descriptions to each cluster center
closest_descriptions = {}
for i in range(10):
    center_vec = kmeans.cluster_centers_[i]
    distances = np.linalg.norm(np.array(embeddings) - center_vec, axis=1)
    closest_indices = np.argsort(distances)[:5]
    closest_descriptions[f"Cluster {i+1}"] = [full_desc[idx] for idx in closest_indices]

# Output the closest descriptions
print(json.dumps(closest_descriptions, indent=4))

# Initialize an empty list to store the clusters data
clusters = []

for ii, cluster in enumerate(closest_descriptions.keys()):
    print(f"Generating summary for cluster {cluster}...")
    descriptions = closest_descriptions[cluster]

    request = f"Respond in the format:\nTask Type: summary of type of tasks in this cluster\nExample Task: an example task\nSummaries the following task cluster explain the type of tasks that are present and generating an example task that is indicative of the tasks in this cluster. \n\n Cluster {cluster} \n\n {descriptions[0]} \n\n {descriptions[1]} \n\n {descriptions[2]} \n\n {descriptions[3]} \n\n {descriptions[4]}"

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": request}],
    )

    # Append a dictionary with cluster data to the list of clusters
    clusters.append(
        {
            "cluster": cluster,
            "size": int(counts[ii]),
            "summary": response.choices[0].message.content,
        }
    )

# Sort the clusters by size
clusters = sorted(clusters, key=lambda x: x["size"], reverse=True)
with open("cluster_summaries.json", "w") as file:
    import IPython

    IPython.embed()
    json.dump(clusters, file, indent=4)
