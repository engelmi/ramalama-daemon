# ramalama-daemon

Proposal on how to split [RamaLama](https://github.com/containers/ramalama) into multiple components:

- daemon
- worker
- cli

This is roughly depicted in the following diagram:

![overview](./assets/ramalama-daemon.drawio.png)

Both, the `daemon` and the `worker`, would act as a Model Router (similar to [llama-swap](https://github.com/mostlygeek/llama-swap)). The worker does this on a machine basis while the daemon enables routing cross-machine (container, VM, physical host). 

## Supporting model swapping

Support for `Model Swapping` can be added by using a configuration file on the worker side, similar to the one used by [llama-swap](https://github.com/mostlygeek/llama-swap/blob/main/docs/configuration.md). In the most basic scenario, either an unlimited number of models can be served at once or only one. 

## Running the proposal

1. Start the daemon:
```bash
$ PYTHONPATH=. ./daemon/server.py --port 8070
```

2. Start the (local) worker:
```bash
$ PYTHONPATH=. ./worker/server.py --daemon-port 8070
```

3. Open the webbrowser at `http://localhost:8070/ui`. You should see a list of the registered, local worker and all available models. By clicking on a `Start`-button, the model can be run. 

## Generating OpenAPI clients

First, install OpenAPI spec to python client:
```bash
$ npm install @openapitools/openapi-generator-cli -g
```

Then run

```bash
$ make generate
```
