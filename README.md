Circles of Influence
====================

The most popular posts and profiles on Google+

## Installation

1. Make sure that you have up-to-date versions of [Docker Engine](https://docs.docker.com/engine/installation/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

2. Get the source:
  * `git clone https://github.com/patrickhoefler/coi.git`

3. Change the working directory:
  * `cd coi`

4. Prepare docker-compose.yml:
  * `cp docker-compose.template.yml docker-compose.yml`
  * In the new `docker-compose.yml`:
    * Set `GOOGLE_API_KEY` (which you can create and look up at https://console.developers.google.com/)
    * Set `DJANGO_SECRET_KEY` to some random string

5. Start *Circles of Influence*:
  * `docker-compose up -d`
