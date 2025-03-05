load("ext://helm_resource", "helm_resource")

helm_resource(
    "directory-importer",
    chart="./helm/directory-importer/",
    deps=[
      "tilt-values.yaml",
      "helm/directory-importer/",
    ],
    flags=[
      "--values", "tilt-values.yaml"
    ],
    image_deps=[
      "artifacts.software-univention.de/nubus-dev/images/directory-importer:latest",
    ],
    image_keys=[
      ("image.registry", "image.repository", "image.tag"),
    ],
)

docker_build(
    "artifacts.software-univention.de/nubus-dev/images/directory-importer:latest",
    "./",
    dockerfile="./docker/directory-importer/Dockerfile",
)
