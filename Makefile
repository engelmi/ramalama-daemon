
clean:
	rm -rf openapi/daemon/
	rm -rf openapi/worker/

	mkdir -p openapi/daemon/
	mkdir -p openapi/worker/

generate: clean generate-openapi-spec generate-openapi-clients
	

generate-openapi-spec:
	PYTHONPATH=. python ./openapi/generate.py

generate-openapi-clients: generate-daemon-client generate-worker-client

generate-daemon-client:
	openapi-generator-cli \
		generate \
		-i openapi/daemon/openapi.json \
		-g python \
		-o openapi/daemon/client \
		--additional-properties=packageName=worker.client.daemon,projectName=daemon-client
	
	rm -rf worker/client/daemon
	cp -r openapi/daemon/client/worker/client/daemon worker/client/daemon

generate-worker-client:
	openapi-generator-cli \
		generate \
		-i openapi/worker/openapi.json \
		-g python \
		-o openapi/worker/client \
		--additional-properties=packageName=daemon.client.worker,projectName=worker-client
	
	rm -rf daemon/client/worker
	cp -r openapi/worker/client/daemon/client/worker daemon/client/worker
