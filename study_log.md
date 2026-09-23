# Study Log

Running reference built from real study sessions, across whatever you're currently curious about. Newest entry is on top within each subject.

## Business Analysis
**RICE Score Framework and Practice Examples** _RICE Scoring_ &mdash; 2026-09-21

- RICE score divides by Effort because we want a unit of measurement that answers "total impact per time worked"; this implies a project requiring lots of person-months would yield relatively minimal impact per time worked
- Project/task idea: Open a hot dog stand at an intersection near a mall in town
  - R - 10-20 people pass by every 1-2 minutes; using the upper end of that range as a single reach estimate for a defined ~1-minute period, R ≈ 18
  - R (alternate pass) - 10-20 people stopped at the intersection every 1-2 minutes, using R = 15 as a single estimate
  - I - Medium impact of 1x
  - C - Medium low confidence = 70%
  - E - Upkeep and sales of hot dog stand, materials, paperwork, permit... 2 person-months
  - RICE score = (18 * 1 * 0.7) / 2 = 6.3, or roughly 6.5
  - RICE score (with R=15) = (15*1*0.7)/2 = 5.25
  - On a later pass, re-estimated Effort as 1 person-month instead of 2, giving RICE score = (15*1*0.7)/1 = 10.5
- First project/task idea: Open a pizza shop near the beach
  - R - 20-30 people every half hour
  - I - High impact (2x) especially if the pizza is good
  - C - Medium low confidence = 60-70%
  - E - Upkeep and sales of restaurant, materials, paperwork, permit... 2 person-months
  - RICE score = (25*2*0.65)/2 = 16.25
- Second project/task idea: Open an ice cream shop near the beach
  - R - 20-30 people every half hour
  - I - High impact (2.5x) especially if ice cream is good and the weather is hot
  - C - Medium low confidence = 60-70%
  - E - Upkeep and sales of restaurant, materials, paperwork, permit... 2 person-months
  - RICE score = (25*2.5*0.65)/2 = 20.3125
  - Gave the ice cream shop a higher Impact multiplier because it's in a beach town in California where the weather is warm most of the year, and because there are already a lot of pizza shops in town, so the ice cream shop has higher impact and should be prioritized first
- The Confidence factor is meant to correct for estimation error or lack of specific data backing the chosen score for R, I, C, and E
  - Example: opening a bakery in town where Reach and Impact are estimated high but Confidence is low - this risks being a project high in ambition but low in practical execution; Confidence curbs the enthusiasm of the project idea when terms are ill-defined

**User Stories: Structure, Purpose, and 3Cs** _User Story_ &mdash; 2026-09-18

- A user story comprises persona + need + purpose; it's a short sentence in the form "As a [persona], I [want to], [so that]" meant to communicate value from a project or task. (Note: source material also gives a slightly different phrasing - "As a [user], I want [goal] so that [reason/benefit]" - both refer to the same underlying structure, just worded differently.)
- Beyond the format, a full user story also includes: a brief description of the desired functionality, the user's perspective, and acceptance criteria (the conditions that define when the story is considered complete).
- The 3Cs of a user story: Card (the written description itself), Conversation (the discussions that clarify details), and Confirmation (the acceptance criteria that define when the story is done).

**BRD vs FRD, SMART Objectives, and Scope Creep** _BRD_ &mdash; 2026-09-07

- The executive summary should be written last, so once the BRD is complete, the executive summary can comprehensively cover the essential components of the project. If written first, it risks being incomplete or inaccurate, since it may miss or misrepresent details that only emerge as the rest of the BRD (objectives, scope, requirements, etc.) is finalized
- SMART project objective example: track number of users in the first quarter and increase enrollment by 10-15% for the next quarter; another phrasing: increase users engaging with the new app feature by 10-15% between quarter 1 and 2; another phrasing: track user engagement with the new app feature, comparing performance metrics like log in rate and minutes of use, between quarter 1 and 2, aiming for 10% increased engagement from app compared to without the new feature
- Project constraint example: availability of technical team for user tracking and customer experience team for retention and outreach strategies
- BRD vs FRD comparison:
  - BRD: audience is primarily business stakeholders/executives, created before FRD (i.e., earlier in process), technical detail is more broad and high level
  - FRD: audience is primarily technical/development teams, created after BRD, technical detail is high, listing how to do specific tasks related to the project
- Scope creep is when a project expands beyond the established boundaries and becomes hard to control
- The project scope section is important because it defines the boundaries of a project; having agreed-upon deliverables/timeline/budget gives a reference point to evaluate and reject out-of-bounds requests
- Real scenario: a mobile app feature project expands to include an additional mobile app feature - this is scope creep because the focus should be on only one mobile app feature

**BRD Purpose, Structure, and Executive Summary** _BRD_ &mdash; 2026-09-05

- A Business Requirements Document (BRD) is a high level document listing out the goals and scope of a project, meant to guide and support all stakeholders involved.
- The executive summary appears first in a BRD because it is the thesis or main aim of the project consolidated into one statement.
- The reason it is written last is so that, upon completing the BRD, the executive summary is set to incorporate and distill all elements of the BRD into one line.
- Example project: Launching a new app feature in Second Pass where users can input hand-written notes for the AI to analyze, confirm, and consolidate.
  - Business requirements: increase engagement by 10% by end of the quarter
  - Project scope: users of Second Pass, team members, project manager
  - Project constraints: cannot go over token budget if using AI
- BRD vs FRD:
  - BRD - purpose is a high level document meant to guide and support all stakeholders in the building of a project
  - FRD - purpose is to be a specific, detailed document to support specific teams to accomplish discrete tasks of the project described by the BRD
- Project constraints section lists out the budget, while the cost-benefit analysis section adds onto the budget and gives benefits and expected ROI.
- Don't remember the steps of writing a BRD (need to review).

## Product Management
**Product Vision vs Strategy and Leadership Principles** &mdash; 2026-09-23

- Four parts: (a) make tough decisions on what matters, (b) generate and leverage insights, (c) turn insights into actions, (d) actively manage and don't micro-manage
- A product vision gives direction, and product strategy gives the "how-to" to get there. Having both minimizes micro-managing because everyone has a clear roadmap to the destination, even if their path deviates slightly; what's important is that the overarching goal and destination are accomplished


**Product Discovery vs. Delivery Responsibilities** _Framework_ &mdash; 2026-09-23

- Two overarching responsibilities: product discovery and product delivery
- Product discovery is identifying a problem and a solution; it is a skill of judgement
- Product delivery is building, testing, and deploying the solution to customers; it is a skill of process
- Having a great idea alone does not guarantee a successful product
- Sometimes we get tricked into believing that having a great idea is 90% of the work behind a successful product
- New AI-powered tools make it easier to define requirements, design experiences, and write code, lowering the barrier to building something - but that doesn't mean anyone with an idea can produce a successful product
- So the article's point is that as AI-powered tools take over more of product delivery, product discovery - the judgement-driven work of understanding the problem and finding a good solution - becomes the main activity of product teams; a good idea alone isn't enough because it skips over this discovery work
- The article notes average team size is shrinking by roughly 20-30% due to productivity gains from AI-powered tools
- Gen AI-based tools also broaden the scope of responsibility product teams can take on
