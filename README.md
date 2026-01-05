# ramalama-daemon

Proposal on how to split [RamaLama](https://github.com/containers/ramalama) into multiple components:

- daemon
- worker
- cli

This is roughly depicted in the following diagram:

![overview](./assets/ramalama-daemon.drawio.png)


## Generating OpenAPI clients

First, install OpenAPI spec to python client:
```bash
$ npm install @openapitools/openapi-generator-cli -g
```

Then run

```bash
$ make generate
```
