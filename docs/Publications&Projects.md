---
layout: default
title: Presentations
nav_order: 6
nav_exclude: false
---

# Publications & Featured Projects

The page lists all known publications about PING-Mapper, publications that use PING-Mapper, or projects which are currently utilizing PING-Mapper. If you have used PING-Mapper for your project or used it as part of a publication, please submit additional information on [GitHub](https://github.com/CameronBodine/PINGMapper/discussions/76)

## Publications about the Software

Bodine, C. S., Buscombe, D., Best, R. J., Redner, J. A., & Kaeser, A. J. (2022). PING-Mapper: Open-source software for automated benthic imaging and mapping using recreation-grade sonar. Earth and Space Science, 9, e2022EA002469. [https://doi.org/10.1029/2022EA002469](https://doi.org/10.1029/2022EA002469)

## Publications that Use the Software

Biber, P., Oguntuase, J., Raber, G., & Waldron, M. (2023). Assessing the Effectiveness of Seagrass Detection Using Drone and Sonar Based Methods. OCEANS 2023 - MTS/IEEE U.S. Gulf Coast, 1–6. [https://doi.org/10.23919/OCEANS52994.2023.10337091](https://doi.org/10.23919/OCEANS52994.2023.10337091)

## Projects that Use the Software

### Sidescan Ghosts!
By Adrian Pinchbeck

Halfway through post-processing some Humminbird recordings of an area of mixed ground using PINGMapper and QGIS, something suddenly caught my eye while merging tiles…

I had previously spent a morning mapping a small No Take Zone just off the east coast of England, teaming up a standalone Helix 9 setup, running off a 7Ah alarm battery, with a home-made towfish on a transducer extension cable. A stiff breeze blowing off the land on my starboard side made it tricky to maintain track against an opposing ebbing tide and along a carefully arranged grid of waypoints created earlier. Consequently, I wasn’t really studying the Humminbird screen for any detail, relying on my other navigation electronics hard-wired on the boat, only periodically checking towfish altitude above some areas of pretty rough ground and boulders until I was done.

Back at the computer I processed each separately recorded mile long track using PINGMapper, taking account of both layback (approximated using high school trigonometry) and cross-track error, and then started to process each track on QGIS to start creating a complete mosaic of the zone. Then that something caught my eye, a strange line running along a clean area of smooth sand.

<img src="https://private-user-images.githubusercontent.com/121804798/266104438-b5844bf3-b722-404f-bae6-a7ecae4fd553.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MTA3NzcwMTMsIm5iZiI6MTcxMDc3NjcxMywicGF0aCI6Ii8xMjE4MDQ3OTgvMjY2MTA0NDM4LWI1ODQ0YmYzLWI3MjItNDA0Zi1iYWU2LWE3ZWNhZTRmZDU1My5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjQwMzE4JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI0MDMxOFQxNTQ1MTNaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1jYTU4YjgwMDAzYzljNzYwNmFlZmE1MzAzMTExOWUyNzRiY2NjOGNkNDNjNzFmMTU5ZGYwYmQzZTBmMjNmZGQxJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZhY3Rvcl9pZD0wJmtleV9pZD0wJnJlcG9faWQ9MCJ9.mzVsdSQjHCn_4rEOE-E2Fsuy9RX7wbAgrr_DOgHFtGM"/>

As I zoomed in to investigate further, the line continued in both directions, with periodic lumps along the way. It was clearly a string of around eight pots in an area I didn't expect.

<img src="https://private-user-images.githubusercontent.com/121804798/266116229-a9f1a11c-b43b-4f42-86bd-8979a511f7a0.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MTA3NzcwMTMsIm5iZiI6MTcxMDc3NjcxMywicGF0aCI6Ii8xMjE4MDQ3OTgvMjY2MTE2MjI5LWE5ZjFhMTFjLWI0M2ItNGY0Mi04NmJkLTg5NzlhNTExZjdhMC5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjQwMzE4JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI0MDMxOFQxNTQ1MTNaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1iNDZlODIyYzdjNmFhYjI4YTExZTJiN2U5OTI3ZjAwZjZiZTg1NGM5NTg2YTMxNjg0NjNlYzczMTg0YzQ5NzI2JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZhY3Rvcl9pZD0wJmtleV9pZD0wJnJlcG9faWQ9MCJ9.9t5ITt0MwT5Q2BJcH8FMr7coV6zl7LkGbn-N8iCcojI">

There’s a large crab and lobster fishery in this part of the North Sea, but this was well inside the No Take Zone, so there shouldn’t be any fishing gear in this position at all. Further, I would have spotted any surface marker, had the string had one, and quickly lifted the towfish clear of any potential snags. I hadn’t seen anything, so what was going on?

A quick email to one of the local wreck dive teams with a list of WGS84 numbers for each pot, and they then confirmed that a dive would be made, so the wait for feedback began. Three weeks later, an email from the divers popped up on my feed. All pots had been located, but no anchor or ends were found. Maybe they were just part of a string broken up and relocated in a storm? Pots had clearly been there for some time, at they were found half buried in sand, but the divers opened all hatch doors and various previously doomed critters were set free (pots will continue fishing indefinitely even without any bait).

The next job is to get permission for a commercial potter to access the restricted area, and clear the string out of the No Take Zone using a pot hauler for good.