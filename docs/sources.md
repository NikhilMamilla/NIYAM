# Sources for the regulatory and standards facts

Every dated or regulatory claim on the landing page (the block below, read by `npm run site-data`) and in the README is
listed here with the page it was checked against. All pages were accessed on **25 November 2026**. "Primary" means the
issuing body's own page; "secondary" means a report about it. Where only secondary sources could be read, the claim
says so or is worded no more strongly than they support.

## Shown on the landing page

<!-- site-data: context. Landing sheet A-02 shows these three bullets verbatim (npm run site-data). -->
- **India.** India: BIS withdrew the National Building Code 2016 with effect from 30 April 2026 and replaced it with the advisory National Building Construction Standards 2026 (SP 7:2026).
- **Singapore.** Singapore: from 1 October 2026, building plan submissions through CORENET X are mandatory for new projects of 5,000 m² gross floor area and above.
- **buildingSMART.** buildingSMART: IDS 1.0, published as a final standard in June 2024, is an open standard for machine-checkable information requirements.
<!-- /site-data: context -->

## Checked claims

| Claim as shown | Status | Source(s) |
|---|---|---|
| India: BIS withdrew the National Building Code 2016 (SP 7:2016) with effect from 30 April 2026 and replaced it with the National Building Construction Standards 2026 (SP 7:2026), which are advisory. | **Verified, secondary sources only.** The Gazette of India notice could not be fetched (TLS certificate error), so the date rests on two secondary reports that agree with each other. | Agile Regulatory, "BIS Update 2026: National Building Code 2016 replaced by SP 7:2026" (31 Oct 2026): "SP 7:2016, has been withdrawn effective 30 April 2026", https://www.agileregulatory.com/latest-updates/bis-update-2026-national-building-code-2016-replaced-by-sp-7-2026 · Drishti IAS, "National Building Construction Standards 2026" (1 May 2026): "voluntary guidelines for building construction and safety rather than legally binding regulations", https://www.drishtiias.com/daily-updates/daily-news-analysis/national-building-construction-standards-2026/print_manually · Gazette notice (not read): https://egazette.gov.in/WriteReadData/2026/272177.pdf |
| Singapore: from 1 October 2026, submissions through CORENET X are mandatory for new projects with GFA of 5,000 m² and above; smaller projects may continue on CORENET 2.0. | **Verified, primary. Corrected:** the earlier text said digital BIM submissions become mandatory for all approvals from 1 October 2026, which URA circular DC26-08 (23 July 2026) narrowed to new projects of 5,000 m² GFA and above. | URA circular DC26-08, "Updates to CORENET X Implementation Plan" (23 Jul 2026): "From 1 October 2026, submission via CORENET X Gateway Processes will be mandatory for all new projects with GFA of 5,000m2 and above.", https://www.ura.gov.sg/guidelines/circulars/dc26-08/ · earlier plan, URA circular DC23-07 (26 Sep 2023), https://www.ura.gov.sg/guidelines/circulars/dc23-07/ |
| buildingSMART: IDS 1.0 was published as a final buildingSMART standard in June 2024. | **Verified.** The release page names it the final standard. The fetched text gave the day ("03 Jun") but not the year, which comes from Wikipedia. | buildingSMART/IDS releases, "v1.0 Final buildingSMART Standard … as approved by the Standards Committee Executive", https://github.com/buildingSMART/IDS/releases · Wikipedia, "version 1.0 was published in June 2024", https://en.wikipedia.org/wiki/Information_Delivery_Specification |
| India's online building-permission systems (OBPS, AutoDCR-type scrutiny) check 2D CAD drawings against the bye-laws, with the rules inside the vendor's software. | **Softened, not verified verbatim.** Search results quote state OBPS portals (Meghalaya eDCR reads AutoCAD files and scrutinises plans "as per the Bye Laws"; West Bengal Smart DCR), but the pages fetched did not show that sentence. The landing page says only that "in most Indian cities, building plans are submitted and checked as 2D drawings" and that automated checks keep the rules inside proprietary software; it names no product. | Meghalaya OBPS instructions, https://obps.meghalaya.gov.in/obps/instructions.htm (fetched: mentions sample DXF drawings only) · Meghalaya OBPS stakeholder toolkit (PDF, not readable as text here), https://obps.meghalaya.gov.in/obps/resources/OBPS_Toolkit_Stakeholder.pdf |
| MBBL 2016: the MoHUA (then Ministry of Urban Development) Model Building Bye-Laws 2016, prepared by TCPO. | **Verified from the source PDF.** The text ingested into the corpus is the MoHUA PDF (not redistributed, `rules/source/`); search results agree on the issuer and the March 2016 release. | MoHUA, https://www.mohua.gov.in/ (official PDF) · NIUA SmartNet copy, https://smartnet.niua.org/node/3447 |
| Telangana Building Rules 2012: G.O.Ms.No.168, MA&UD, dated 07.04.2012. NIYAM uses the original text; later amendments are not applied. | **Verified from the source PDF and secondary listings.** The ingested PDF is the G.O.Ms.No.168 text. Amendments since (for example G.O.Ms.No.49 of 31.03.2023, and a 2026 amendment reported to change the high-rise threshold) are not applied, as the README and landing page say. | Telangana TS-bPASS, G.O.Ms.No.49 dt. 31.03.2023 (amendment to G.O. 168), https://tsbpass.telangana.gov.in/html/docs/go_s_and_act/GO%2049%20dt.31.3.2023%20amendment%20to%20GO%20168.pdf · Telangana Government Orders list, https://buildnow.telangana.gov.in/go-and-act |

## Removed or not used

- "Singapore: Digital BIM submissions for building approvals become mandatory from 1 October 2026." Replaced by the
  narrower DC26-08 wording above.
- No claim about OBPS or AutoDCR names a product, a city count or a speed figure. Vendor speed claims found in search
  results are not used.
