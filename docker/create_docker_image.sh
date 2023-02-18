#!/usr/bin/env bash
set -x
set -e
docker build -f Dockerfile -t fussel ../

echo "What would you like to tag this image with?"
read TAG
docker tag fussel fussel:${TAG}

echo "Would you like to publish? (y/N)"
read DO_PUBLISH
if [ "$DO_PUBLISH" == "y"  ] || [ "$DO_PUBLISH" == "Y" ]
then
	docker tag fussel:${TAG} ghcr.io/cbenning/fussel:${TAG}
	docker push ghcr.io/cbenning/fussel:${TAG}
else
	exit 0
fi

echo "Would you like to mark as latest? (y/N)"
read DO_LATEST
if [ "$DO_LATEST" == "y" ] || [ "$DO_LATEST" == "Y" ]
then
	docker tag ghcr.io/cbenning/fussel:${TAG} ghcr.io/cbenning/fussel:latest
	docker push ghcr.io/cbenning/fussel:latest
else
	exit 0
fi

