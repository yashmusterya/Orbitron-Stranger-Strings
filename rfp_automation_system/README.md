# RFP Automation System

This system automates the response to Request for Proposals (RFPs) using a multi-agent workflow.

## Workflow

1.  **Orchestrator (Main Agent)**: Coordinates the process.
2.  **Sales Agent**: Scrapes RFP details from a URL.
3.  **Technical Agent**: Matches requirements with `data/inventory.json`.
4.  **Pricing Agent**: Calculates costs using `data/pricing_rules.json`.
5.  **Final Response Agent**: Generates the final proposal.

## Usage

Provide a URL to the Orchestrator to begin.
