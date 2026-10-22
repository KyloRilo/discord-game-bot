# Discord Game Bot

This repository will perform the following functions:
* Define and build docker images for running servers of games which will be pushed to ECR
* Defines an discord bot based as an AWS Lambda
* Pushes docker builds of lambda to ECR

## Design

### Functional Requirements:
* The bot should be able to...
* * Spin up/down game servers using ECR images, as ECS tasks
* * Provide current session info, such as uptime, connectivity details, and server credentials
* The bot only enables the launch of one game's server at a time

### Nonfunctional Requirements:
* When a server spins up...
* * Generates a new login token for said server (in AWS secretsmanager)
* * Creates an eventbridge cron which hits the game bot lambda with an activity check at a specified interval
* * Maintains routine save backups
* When a server spins down...
* * Ensures final save backup
* * Disables activity check eventbridge cron
* * Erases old server login token from secretsmanager

### Infra Requirements:
* Everything is to be built using docker
* Discord bot will be connected via webhook to an AWS Lambda
* Servers hosted as ECS tasks

# Game Catalog

[Valheim](build/valheim/)
[Windrose](build/windrose/) (Not yet enabled)
[Minecraft](build/mionecraft/) (Future item)