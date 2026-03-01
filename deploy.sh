#!/bin/bash

MSG_UPDATE="[exam session api , import csv] fix start exam with daily plan & enhance import can using setId from exits flash card set "
# Exit immediately if a command exits with a non-zero status
set -e
git pull origin main
echo "Staging changes..."
git add .

echo "Committing changes..."
git commit -m "update ${MSG_UPDATE}"

echo "Fetching tags and updates..."
git fetch --tags

echo "Getting the latest tag..."
LAST_TAG=$(git tag | sort -V | tail -n 1)
echo "Latest tag: $LAST_TAG"

IFS='.' read -r MAJOR MINOR PATCH <<< "${LAST_TAG//v/}"
PATCH=$((PATCH + 1))
NEW_TAG="v${MAJOR}.${MINOR}.${PATCH}"
echo "New tag: $NEW_TAG"

echo "Creating new tag..."
git tag $NEW_TAG

echo "Pushing changes and tags to the repository..."
git push origin main
git push origin $NEW_TAG

echo "Deployment complete!"
