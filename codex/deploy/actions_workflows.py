manual_deploy = """
name: cloudrun-deploy
#on:
#  push:
#    branches:
#      - master
on: workflow_dispatch
jobs:
  setup-build-publish-deploy:
    name: Setup, Build, Publish, and Deploy
    runs-on: ubuntu-latest
    steps:
    - name: Checkout
      uses: actions/checkout@master

    - name: Authenticate to Google Cloud with token exchange
      uses: google-github-actions/auth@v1
      with:
        token_format: 'access_token'
        create_credentials_file: 'true'
        service_account: ${{ secrets.GCP_EMAIL }}
        credentials_json: ${{ secrets.GCP_CREDENTIALS }}

    # Configure Docker with Credentials
    - name: Configure Docker
      run: |
        gcloud auth configure-docker

    - name: Install Cloud SQL Proxy
      run: |
        wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
        chmod +x cloud_sql_proxy

    - name: Start Cloud SQL Proxy
      run: |
        ./cloud_sql_proxy -instances=${{ secrets.CLOUD_SQL_CONNECTION_NAME }}=tcp:5432 &
        sleep 10  # Wait for the Cloud SQL Proxy to be fully ready

    - name: Run Migrations
      run: |
        export DATABASE_URL="postgresql://${{ secrets.DB_USER }}:${{ secrets.DB_PASS }}@localhost:5432/${{ secrets.DB_NAME }}"
        npm install prisma -g
        prisma migrate deploy

    # Build the Docker image
    - name: Build & Publish
      run: |
        # Set the Google Cloud project
        gcloud config set project ${{ secrets.GCP_PROJECT }}

        REPO_NAME="${{ github.event.repository.name }}"
        REPO_NAME="${REPO_NAME,,}"

        IMAGE_TAG="gcr.io/${{ secrets.GCP_PROJECT }}/${REPO_NAME}:${GITHUB_RUN_NUMBER}"

        # Submit the build to Google Cloud Build
        gcloud builds submit --tag $IMAGE_TAG

        # Set the default region for Google Cloud Run deployments
        gcloud config set run/region us-central1

    - name: Deploy to Google Cloud Run
      run: |
        REPO_NAME="${{ github.event.repository.name }}"
        REPO_NAME="${REPO_NAME,,}"  
        IMAGE_NAME="gcr.io/${{ secrets.GCP_PROJECT }}/${REPO_NAME}:${{ github.run_number }}"

        gcloud run deploy ${REPO_NAME} \
          --image $IMAGE_NAME \
          --platform managed \
          --allow-unauthenticated \
          --memory 512M \
          --port 8000 \
          --add-cloudsql-instances ${{ secrets.CLOUD_SQL_CONNECTION_NAME }} \
          --set-env-vars "DATABASE_URL=postgresql://${{ secrets.DB_USER }}:${{ secrets.DB_PASS }}@localhost/${{ secrets.DB_NAME }}?host=/cloudsql/${{ secrets.GCP_PROJECT }}:us-central1:${{ secrets.SQL_INSTANCE_NAME }}" \
          --set-env-vars "INSTANCE_CONNECTION_NAME=${{ secrets.CLOUD_SQL_CONNECTION_NAME }}"

""".lstrip()

auto_deploy = """
name: cloudrun-deploy
on:
 push:
   branches:
     - master
jobs:
  setup-build-publish-deploy:
    name: Setup, Build, Publish, and Deploy
    runs-on: ubuntu-latest
    steps:
    - name: Checkout
      uses: actions/checkout@master

    - name: Authenticate to Google Cloud with token exchange
      uses: google-github-actions/auth@v1
      with:
        token_format: 'access_token'
        create_credentials_file: 'true'
        service_account: ${{ secrets.GCP_EMAIL }}
        credentials_json: ${{ secrets.GCP_CREDENTIALS }}

    # Configure Docker with Credentials
    - name: Configure Docker
      run: |
        gcloud auth configure-docker

    - name: Install Cloud SQL Proxy
      run: |
        wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
        chmod +x cloud_sql_proxy

    - name: Start Cloud SQL Proxy
      run: |
        ./cloud_sql_proxy -instances=${{ secrets.CLOUD_SQL_CONNECTION_NAME }}=tcp:5432 &
        sleep 10  # Wait for the Cloud SQL Proxy to be fully ready

    - name: Run Migrations
      run: |
        export DATABASE_URL="postgresql://${{ secrets.DB_USER }}:${{ secrets.DB_PASS }}@localhost:5432/${{ secrets.DB_NAME }}"
        npm install prisma -g
        prisma migrate deploy

    # Build the Docker image
    - name: Build & Publish
      run: |
        # Set the Google Cloud project
        gcloud config set project ${{ secrets.GCP_PROJECT }}

        REPO_NAME="${{ github.event.repository.name }}"
        REPO_NAME="${REPO_NAME,,}"

        IMAGE_TAG="gcr.io/${{ secrets.GCP_PROJECT }}/${REPO_NAME}:${GITHUB_RUN_NUMBER}"

        # Submit the build to Google Cloud Build
        gcloud builds submit --tag $IMAGE_TAG

        # Set the default region for Google Cloud Run deployments
        gcloud config set run/region us-central1

    - name: Deploy to Google Cloud Run
      run: |
        REPO_NAME="${{ github.event.repository.name }}"
        REPO_NAME="${REPO_NAME,,}"  
        IMAGE_NAME="gcr.io/${{ secrets.GCP_PROJECT }}/${REPO_NAME}:${{ github.run_number }}"

        gcloud run deploy ${REPO_NAME} \
          --image $IMAGE_NAME \
          --platform managed \
          --allow-unauthenticated \
          --memory 512M \
          --port 8000 \
          --add-cloudsql-instances ${{ secrets.CLOUD_SQL_CONNECTION_NAME }} \
          --set-env-vars "DATABASE_URL=postgresql://${{ secrets.DB_USER }}:${{ secrets.DB_PASS }}@localhost/${{ secrets.DB_NAME }}?host=/cloudsql/${{ secrets.GCP_PROJECT }}:us-central1:${{ secrets.SQL_INSTANCE_NAME }}" \
          --set-env-vars "INSTANCE_CONNECTION_NAME=${{ secrets.CLOUD_SQL_CONNECTION_NAME }}"

""".lstrip()
