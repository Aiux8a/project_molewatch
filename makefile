# Include environment variables from .env
-include .env
export

# Build the Docker image locally
build_container_local:
	docker build -t $(IMAGE):dev .

# Run the Docker container locally
run_container_local:
	docker run -it -p 8080:8080 -e PORT=8080 $(IMAGE):dev

# Submit the build to GCP Cloud Build
gcp_build:
	gcloud builds submit --tag $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACTSREPO)/$(IMAGE):latest

# Deploy the image to GCP Cloud Run
gcp_deploy:
	gcloud run deploy $(IMAGE) \
		--image $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT)/$(ARTIFACTSREPO)/$(IMAGE):latest \
		--memory $(MEMORY) \
		--platform managed \
		--allow-unauthenticated
