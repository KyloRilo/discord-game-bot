# Build
`docker build -t valheim-server .`

# Run
`docker run -d   --name valheim   -p 2456-2458:2456-2458/udp   -e SERVER_NAME="Valhalla"   -e WORLD_NAME="Midgard"   -e SERVER_PASS="supersecret"   valheim-server`