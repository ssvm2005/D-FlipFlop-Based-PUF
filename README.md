# Design and Analysis of a D Flip-Flop Based Physically Unclonable Function (PUF) Circuit

A transistor-level study of D Flip-Flop-based Physical Unclonable Functions (PUFs) for hardware authentication, using Cadence Virtuoso, the SCL 180 nm PDK, and Python-based statistical analysis.

## Overview

A **Physically Unclonable Function (PUF)** uses small, inherent manufacturing variations in integrated circuits to produce device-specific responses. These responses can support hardware identification and authentication without requiring a permanently stored secret key.

This project studies conventional and symmetric D Flip-Flop PUF architectures, evaluates their responses under process variation and operating-condition changes, and explores a modified circuit architecture. The goal is to understand the trade-offs among response uniqueness, reliability, uniformity, and bit aliasing.

## Architecture

<img width="566" height="389" alt="image" src="https://github.com/user-attachments/assets/cbcd5d6d-71ca-4ff2-968f-9b7f75cd48d5" />

## Tools and Technologies

<img width="405" height="331" alt="image" src="https://github.com/user-attachments/assets/bc362050-b5dd-4448-96d1-6890d5a3beaf" />

## PUF Performance Metrics

The exported response data is evaluated using four key metrics:

- **Uniqueness:** Measures how different the responses of different simulated chip instances are for the same challenge. An ideal average inter-chip Hamming distance is approximately 50%.
- **Reliability:** Measures whether the same chip produces a consistent response under changed operating conditions. An ideal reliability is 100%.
- **Uniformity:** Measures the proportion of 1s in a response. An ideal value is approximately 50%.
- **Bit aliasing:** Measures how often a particular response-bit position is 1 across simulated chip instances. An ideal value is approximately 50%.

<img width="582" height="311" alt="Screenshot 2026-10-20 184529" src="https://github.com/user-attachments/assets/7a30abbf-1a69-4512-b5d2-d8978e34175d" />





