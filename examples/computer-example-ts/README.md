# cua-cloud-openai Example

This example demonstrates how to control a c/ua Cloud container using the OpenAI `computer-use-preview` model and the `@trycua/computer` TypeScript library.

## Overview

- Connects to a c/ua Cloud container via the `@trycua/computer` library
- Sends screenshots and instructions to OpenAI's computer-use model
- Executes AI-generated actions (clicks, typing, etc.) inside the container
- Designed for Linux containers, but can be adapted for other OS types

## Getting Started

1. **Install dependencies:**

   ```bash
   npm install
   ```

2. **Set up environment variables:**
   Create a `.env` file with the following variables:
   - `OPENAI_KEY` — your OpenAI API key
   - `CUA_KEY` — your c/ua Cloud API key
   - `CUA_CONTAINER_NAME` — the name of your provisioned container

3. **Run the example:**

   ```bash
   npx tsx src/index.ts
   ```

## Files

- `src/index.ts` — Main example script
- `src/helpers.ts` — Helper for executing actions on the container

## Further Reading

For a step-by-step tutorial and more detailed explanation, see the accompanying blog post:

➡️ [Controlling a c/ua Cloud Container with JavaScript](https://placeholder-url-to-blog-post.com)

_(This link will be updated once the article is published.)_

---

If you have questions or issues, please open an issue or contact the maintainers.
