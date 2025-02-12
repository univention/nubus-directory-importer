# Changelog

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
