# Worked Examples: Average vs Great

---
disclaimer: >
  These examples are synthetic illustrations, not excerpts from real
  documentation. They demonstrate patterns, not prescriptions. Adapt to
  your context.
---

This file contains side-by-side comparisons of average and great how-to
writing at the step level, the structural level, and the metadata level.
Read this when writing or reviewing to calibrate quality.

---

## 1. Step-Level: The Vague Step vs The Concrete Step

### Average

```markdown
### Step 3: Configure the database

Configure your database connection settings appropriately for your
environment. Make sure the credentials are correct.
```

**Why this fails:**
- "Appropriately" is meaningless — it pushes the hard part onto the reader.
- "Make sure the credentials are correct" is not verifiable.
- No command, no file path, no expected output.
- Violates all four OVER properties (Observable, Verifiable, Executable,
  Reversible).

### Great

```markdown
### Step 3: Configure the database connection

The application reads database credentials from `config/database.yml`.

Open `config/database.yml` and set the following values:

    production:
      host: "db.example.com"
      port: 5432
      database: "myapp_production"
      username: "myapp"
      password: "${DATABASE_PASSWORD}"

Replace `db.example.com` with your database host. Set the
`DATABASE_PASSWORD` environment variable:

    export DATABASE_PASSWORD="your-password-here"

Verify the connection:

    bin/rails db:migrate:status

Expected output (first two lines):

    database: myapp_production
     Status   Migration ID    Migration Name

If you see `could not connect to server: Connection refused`, verify
that your database host is reachable: `pg_isready -h db.example.com -p 5432`.
```

**Why this works:**
- Observable: the file is edited, the env var is set, a command is run.
- Verifiable: expected output is shown, including the first lines.
- Executable: exact file path, exact syntax, exact command.
- Failure path: the most common error is addressed with a diagnostic.

---

## 2. Step-Level: The Inline Lecture vs The Linked Explanation

### Average

```markdown
### Step 4: Enable TLS

TLS (Transport Layer Security) is a cryptographic protocol designed to
provide communications security over a computer network. It is the
successor to SSL (Secure Sockets Layer). TLS uses a combination of
symmetric and asymmetric cryptography to establish a secure connection.
The handshake process involves the client sending a ClientHello message,
the server responding with a ServerHello and its certificate, followed
by key exchange. Understanding this process is important because...

[3 more paragraphs]

To enable TLS, run:

    ./configure --enable-tls
```

**Why this fails:**
- The reader came to enable TLS. They didn't come for a cryptography
  lecture. This is explanation content embedded in a how-to step.
- The 4+ paragraphs consume working memory that should be allocated to
  executing the step.
- Extraneous cognitive load: high. Germane load served: zero (wrong
  context for learning).

### Great

```markdown
### Step 4: Enable TLS

TLS encrypts traffic between the client and server. For background on
how TLS works, see [TLS Explained](/docs/concepts/tls).

Generate a self-signed certificate (for development only):

    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem \
      -days 365 -nodes -subj "/CN=localhost"

Enable TLS in the server configuration (`server.conf`):

    tls.enabled = true
    tls.cert_file = "/path/to/cert.pem"
    tls.key_file = "/path/to/key.pem"

Restart the server:

    systemctl restart myserver

Verify TLS is active:

    curl -k https://localhost:8443/healthz

Expected output:

    {"status": "ok", "tls": true}

If you see `SSL: CERTIFICATE_VERIFY_FAILED`, the `-k` flag was
omitted (it skips certificate verification for self-signed certs).
```

**Why this works:**
- One sentence of context + a link for the curious.
- Three actions, each with a command and expected result.
- Failure path for the most common mistake.
- Zero extraneous load.

---

## 3. Structural Level: The Scope Creep Guide vs The Bounded Guide

### Average — Title: "Docker Networking"

```
1. Installing Docker
2. What is Docker?
3. Docker architecture overview
4. Understanding container networking
5. Bridge networks explained
6. Overlay networks explained
7. Host networks explained
8. Macvlan networks explained
9. Creating a custom bridge network
10. Connecting containers to the network
11. DNS resolution in Docker networks
12. Troubleshooting network issues
13. Advanced networking patterns
14. Docker Compose networking
15. Kubernetes networking comparison
```

**Why this fails:**
- Steps 1-2 are tutorial content (getting started).
- Steps 3-8 are explanation content (understanding concepts).
- Steps 9-10 are the actual how-to.
- Steps 11-15 are a mix of reference and explanation.
- The reader who needs to connect two containers has to wade through
  15 sections to find the 2 that matter.

### Great — Title: "How to route traffic between two Docker containers on a custom bridge network"

```
Prerequisites:
- Docker Engine >= 24.0
- Two container images ready to deploy

Steps:
1. Create a custom bridge network
2. Start the first container on the custom network
3. Start the second container on the same network
4. Verify inter-container connectivity
5. (Optional) Expose a port to the host

Verification:
- End-to-end connectivity check

Troubleshooting:
- "Network not found" error
- Containers can't resolve each other by name
- Port conflict on the host

Next Steps:
- Link: "Understanding Docker network drivers" (explanation)
- Link: "Docker network CLI reference" (reference)
- Link: "How to configure Docker Compose networking" (how-to)
```

**Why this works:**
- Title names the exact outcome.
- 5 steps, each one action.
- Tutorial content eliminated (prerequisites handle it).
- Explanation content linked, not inlined.
- Reference content linked, not duplicated.
- Troubleshooting covers the three most common failures.

---

## 4. Metadata Level: The Zombie Guide vs The Living Guide

### Average

```markdown
# Setting Up CI/CD with Jenkins

Follow these steps to set up Jenkins...
```

No date, no versions, no prerequisites, no author, no disclaimer.
The reader has no way to assess whether this guide is current, who
verified it, or what environment it was tested in.

### Great

```markdown
---
disclaimer: >
  No information within this document should be taken for granted.
  Verify all steps against your own environment.
last_verified: 2026-03-15
verified_on:
  os: "Ubuntu 22.04 LTS"
  jenkins: "2.440.1 LTS"
  java: "OpenJDK 17.0.10"
  docker: "25.0.3"
author: "Platform Engineering Team"
---

# How to configure a Jenkins pipeline for a Dockerized Node.js application

## Overview

This guide configures a declarative Jenkins pipeline that builds,
tests, and deploys a Dockerized Node.js application to a staging
environment.

## Prerequisites

1. Jenkins 2.440.x LTS installed and running
   (`http://your-jenkins:8080` returns the dashboard)
2. Docker 25.x installed on the Jenkins host
   (`docker --version` on the Jenkins host)
3. ...
```

**Why this works:**
- The reader can immediately assess freshness (verified 4 weeks ago).
- Versions are pinned — if the reader has Jenkins 2.450, they know
  the guide might need adaptation.
- The disclaimer sets expectations about reliability.
- Prerequisites are testable commands, not vague assertions.
