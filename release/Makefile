all:
	mkdir generated
	scripts/make_nutanix_manifest.sh demo/manifest.yml generated/deepomatic-demo-manifest.yml
	scripts/make_nutanix_manifest.sh runtime/manifest.yml generated/deepomatic-app-manifest.yml
	zip generated/manifests.zip generated/deepomatic-demo-manifest.yml generated/deepomatic-app-manifest.yml
