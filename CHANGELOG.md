# Changelog

## [1.4.0](https://git.knut.univention.de/univention/dev/projects/directory-importer/compare/v1.3.1...v1.4.0) (2025-05-11)


### Features

* move and upgrade ucs-base-image to 0.17.3-build-2025-05-11 ([4ff65fd](https://git.knut.univention.de/univention/dev/projects/directory-importer/commit/4ff65fdf86e32816bfc4139eda8cabeb4995dd60))

## [1.3.1](https://git.knut.univention.de/univention/dev/projects/directory-importer/compare/v1.3.0...v1.3.1) (2025-05-10)


### Bug Fixes

* missing variable for ldap-server in tests docker-compose.yml ([08d90a5](https://git.knut.univention.de/univention/dev/projects/directory-importer/commit/08d90a555e562e3436e033ec42ed0b9dfa8f07dd))
* move addlicense pre-commit hook ([7fb4428](https://git.knut.univention.de/univention/dev/projects/directory-importer/commit/7fb4428c3aa95b9129a6af5e1741ad4118e2111a))
* move docker-services ([366d127](https://git.knut.univention.de/univention/dev/projects/directory-importer/commit/366d127f6176a83c00d4760d6c6b8880f2e7fd64))
* update common-ci to main ([b5279ce](https://git.knut.univention.de/univention/dev/projects/directory-importer/commit/b5279ceae6d47277d11e8d5eebe583c55a40a027))

## [1.3.0](https://git.knut.univention.de/univention/dev/projects/directory-importer/compare/v1.2.3...v1.3.0) (2025-04-29)


### Features

* Bump ucs-base-image version ([b58f735](https://git.knut.univention.de/univention/dev/projects/directory-importer/commit/b58f7351f8aa0dbd60f6a7fb24e1b9e07b6b57cb)), closes [univention/dev/internal/team-nubus#1155](https://git.knut.univention.de/univention/dev/internal/team-nubus/issues/1155)

## [1.2.3](https://git.knut.univention.de/univention/dev/projects/directory-importer/compare/v1.2.2...v1.2.3) (2025-04-02)


### Bug Fixes

* **deps:** Bump version of pytest-helm and helm-test-harness ([f2173c8](https://git.knut.univention.de/univention/dev/projects/directory-importer/commit/f2173c8d9db99b403eed1e10fed13ba458c2bfab)), closes [univention/dev/internal/team-nubus#1096](https://git.knut.univention.de/univention/dev/internal/team-nubus/issues/1096)
* **helm directory-importer:** Fix helm deployment ([1f66752](https://git.knut.univention.de/univention/dev/projects/directory-importer/commit/1f667524b930b7e0ab38b26287ce9c4d0634ea2f)), closes [univention/dev/internal/team-nubus#1096](https://git.knut.univention.de/univention/dev/internal/team-nubus/issues/1096)

## [1.2.2](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v1.2.1...v1.2.2) (2025-03-20)


### Bug Fixes

* **helm-test:** Adjust to updated testing library ([d92d473](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/d92d47314491d5d9dbb896de9fd038fc642e34ee))
* **helm:** make either password or existingSecret required ([e55c1f7](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/e55c1f776f2830e5fc8ee8e12cab5717c8d03756))
* **helm:** Make loggingConfig optional ([d90a6a9](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/d90a6a92ad538690307f384ba14d433330b67766))
* **helm:** Split pod and container security context and adapt securityContext configuration to the nubus standard ([2cb1b07](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/2cb1b07d18a42975a6f1c23182a5c2976f74b042))
* **helm:** Template namespace on deployments aswell ([06e4fa8](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/06e4fa800d201e3d1a41735ad8e753b83d057220))

## [1.2.1](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v1.2.0...v1.2.1) (2025-03-07)


### Bug Fixes

* build and publish the helm chart in CI ([db95957](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/db95957171a73564df71e1bea9fd55c88f2301cf))

## [1.2.0](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v1.1.0...v1.2.0) (2025-03-06)


### Features

* Initial helm chart templates ([7a1c94a](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/7a1c94ad4e799f49f9cef90d0ffef773cad84af1))


### Bug Fixes

* Clean up helm chart and try to implement best-practices ([67f3501](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/67f35014338e66dfd03366b53b0dc1823c900c96))
* Deduplicate label templating ([c6af031](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/c6af0316dc3a326a9a34521805cc18c9b1bc56e1))
* Dockerignore to trigger fewer container rebuilds ([52a15e3](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/52a15e3e80fce50acbe26a3337dc4ae8d0f92725))
* Implement best-practices from pairing with Johannes B ([0e26be5](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/0e26be537097c339d3c81a24e6d6577fa9ba9a94))
* Mount config file configmap into directory-importer pod ([67854ee](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/67854ee98b404c40f316f48e607963af78473e7f))
* Set the password in the config file to null to make it clearer that it's provided by env values ([6524996](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/65249967c0f09f0169476983218bb14de421e91a))

## [1.1.0](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v1.0.0...v1.1.0) (2025-02-26)


### Features

* Bump ucs-base-image to use released apt sources ([da25cd9](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/da25cd9317f63b5ab5e4e50f443a21160a26a47f))

## [1.0.0](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.6.1...v1.0.0) (2025-02-12)


### ⚠ BREAKING CHANGES

* trigger the directory importer 1.0.0 version bump

### Features

* Update the project version to 1.0.0 ([40b88f7](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/40b88f77c3d670458b17e8f4074a731b4123d956))

## [0.6.1](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.6.0...v0.6.1) (2025-02-11)


### Bug Fixes

* Handle failures during requests to the source LDAP correctly ([9b45f86](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/9b45f864734d74d8bfd6e98a6995881ca5b6cc0f))
* Make the repeater actually repeat after source_search throws an exception ([4ee8087](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/4ee808794f92d4c6b09dc8b82e429497a4caefe2))

## [0.6.0](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.5.0...v0.6.0) (2025-02-07)


### Features

* **load-test:** Jupyter notebook to create load test graphs from log files ([82fd164](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/82fd164459a6e5d5ee2b1764068cb2852c7bb15a))


### Bug Fixes

* **load-test:** Add cleanup functionality to load testing script ([e49b68a](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/e49b68a99546b0275be60bf699b8132aac844f61))
* **load-tests:** final fixes ([6982c7f](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/6982c7f7eb9e572ad149a0e8471e693675b2a792))
* **load-test:** simple import fixes ([c33d848](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/c33d8489b89a6d442d5bdb827058e8cc5d7e57d5))
* Resync every 5 minutes in the example docker compose ([33e892e](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/33e892ee8fe1164586f13351e377e7fbf96f1457))

## [0.5.0](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.4.0...v0.5.0) (2025-02-07)


### Features

* Allow passing credentials as environment variables ([81e8d12](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/81e8d12662de0e81be11f2eb25862fd96f34f3a7))

## [0.4.0](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.3.0...v0.4.0) (2025-01-30)


### Features

* Activate venv by default via entrypoint.d ([9c1d715](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/9c1d715303bf999ef2c3b7fcd1dde07469cf67f6))
* Add logging output into the class "Repeater" ([f9c6172](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/f9c617215551e14384838915428227e1f6dc5f15))
* Add utility class "Repeater" ([d1bec13](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/d1bec133922899a111ea433f73dec9415231b199))
* Allow to specify a custom delay between repeated runs ([cd25c32](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/cd25c32cd5438dc6bbe1f10e51e27fe6d1b948b1))
* Allow to switch on "repeat" mode to run the sync repeatedly ([464e064](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/464e06495c73db84b204c574b74af8521661f9f0))
* Consolidate executable name to "directory-importer" ([b26f2ab](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/b26f2abb0d15b5cc9652391bbfab8cc3d82b2ef2))
* Ensure that the configuration file is a file and can be read ([9e1f11b](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/9e1f11bf176e062a06d04b9905aa0e41e9f33f51))
* Read configuration file name via typer ([65e343a](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/65e343aa02c24266a5ad0972f59e1681f593c519))


### Bug Fixes

* Add user and group "app" with ID 1000 ([ea367a5](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/ea367a5144b72008fc230153b21dcc0d5e593a0e))
* Call udm-directory-importer script directly ([1af2b12](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/1af2b1220345019b4a09807d0328ffa42de8fb94))

## [0.3.0](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.2.1...v0.3.0) (2025-01-30)


### Features

* Add much more group configurability to the ad provisioner and refactor it in the process ([6b3ac01](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/6b3ac0110223e0ba4e6f8e8ae409ff62f722fbeb))


### Bug Fixes

* Fix ad provisioner script after refactoring ([ad0c47f](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/ad0c47feb0e7c51d40db6e907831a2731b9f5720))
* Fix the python packaging configuration so that the .py sources are included ([8bf0ccd](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/8bf0ccdd76ad318d62290a9c7fe98cb4a7178a50))

## [0.2.1](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.2.0...v0.2.1) (2025-01-29)


### Bug Fixes

* Rename udm connector to directory importer ([85a2f6b](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/85a2f6b76863667b697e3bb36dca93cad6313a7c))

## [0.2.0](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.1.0...v0.2.0) (2025-01-22)


### Features

* user local junkaptor ([da97c09](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/da97c09d8035dc5498f2edf25a8f5efa9226061e))

## [0.1.0](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.0.2...v0.1.0) (2025-01-20)


### Features

* standard nubus logging setup ([f75d623](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/f75d62306d0a8e5785b2c194817fcd4f0a3cb636))

## [0.0.2](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/compare/v0.0.1...v0.0.2) (2025-01-16)


### Bug Fixes

* BSI compliance ([d9f9b17](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/d9f9b1712cff9c17f82118e8e40ceb29ceeb1187))

## 0.0.1 (2025-01-09)


### Features

* working dockerfile and docker compose ([a4b2059](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/a4b2059b562cd6a728d4d06ef16466ddd259b402))


### Bug Fixes

* Clean up Dockerfile ([93d3dac](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/93d3dacf4fa8247b0218080ccc85111301886ea5))
* Finish renaming the container to directory-importer ([8aff7eb](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/8aff7eb8b26d6d8ee4ff000ef5a7da139aec4638))
* Remove file copies between stages and replace it with targeted debian package install ([f1c1833](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/f1c183375131ac0df9ab7117d54fa97c75792a25))
* separate test and production/example docker compose setup ([2844c9e](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/2844c9effe0f86f0c679619f6da2616dd223df2d))
* working config for sync from active directory ([73dbba3](https://git.knut.univention.de/univention/customers/dataport/upx/directory-importer/commit/73dbba3bb3019647cdd11c58c14880644a28d25a))
