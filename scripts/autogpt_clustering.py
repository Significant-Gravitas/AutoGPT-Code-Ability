# type: ignore

import json

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.cluster import KMeans

load_dotenv()


client = OpenAI()

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


def get_tasks_from_database():
    from sqlalchemy import MetaData, Table, create_engine, select

    # Create an engine that connects to PostgreSQL server
    engine = create_engine(
        "postgresql://agpt_live:bnfaHGGSDF134345@localhost:5432/agpt_product"
    )

    # Create a metadata instance
    metadata = MetaData()
    # Declare a table
    tasks_table = Table("tasks", metadata, autoload_with=engine)

    # SQL query
    query = select(tasks_table)
    # Execute the query
    with engine.connect() as connection:
        result = connection.execute(query)
        tasks = [row[1] for row in result]

    embeddings = get_openai_embeddings(tasks)
    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=10, random_state=42)
    kmeans.fit(embeddings)
    # Get cluster labels and count the number of occurrences of each value
    unique, counts = np.unique(kmeans.labels_, return_counts=True)

    # Finding the closest descriptions to each cluster center
    closest_descriptions = {}
    for i in range(10):
        center_vec = kmeans.cluster_centers_[i]
        distances = np.linalg.norm(np.array(embeddings) - center_vec, axis=1)
        closest_indices = np.argsort(distances)[:5]
        closest_descriptions[f"Cluster {i+1}"] = [tasks[idx] for idx in closest_indices]

    # Output the closest
    print(json.dumps(closest_descriptions, indent=4))

    return tasks


get_tasks_from_database()
