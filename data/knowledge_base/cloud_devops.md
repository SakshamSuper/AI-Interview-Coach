# Cloud Infrastructure, Containers, and CI/CD

## Containerization with Docker
Containers package application code, runtime, system tools, and libraries together, ensuring parity between development and production.
- Dockerfile: Declarative instructions to assemble container images (multi-stage builds reduce final image footprint).
- Image Layers: Read-only filesystems cached during build; instructions like RUN, COPY create new layers.

## Container Orchestration with Kubernetes (K8s)
Kubernetes automates deployment, scaling, and operations of application containers across clusters.
- Pod: Smallest deployable compute unit in Kubernetes representing one or more containers.
- Deployment: Manages replica sets, declarative updates, and self-healing rollouts.
- Service: Abstract way to expose an application running on a set of Pods (ClusterIP, NodePort, LoadBalancer).
- ConfigMaps and Secrets: Separate configuration and sensitive credentials from container image.

## CI/CD Pipelines and Infrastructure as Code (IaC)
- Continuous Integration (CI): Developers frequently merge code into main branch; automated builds and tests run to detect integration errors.
- Continuous Delivery/Deployment (CD): Code is automatically packaged, tested, and staged for release (or pushed directly to production).
- Infrastructure as Code (IaC): Tools like Terraform enable declarative provisioning and lifecycle management of cloud infrastructure.