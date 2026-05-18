
# def generate_tree_refinement_prompt(tree_json):

#     prompt = f"""
# You are an expert JSON tree refinement system.

# Your task is to analyze and correct the provided hierarchical document tree.

# The tree was generated incrementally from separated document contexts,
# so some hierarchy inconsistencies may exist.

# IMPORTANT FIXES REQUIRED:

# 1. Fix parent-child page range consistency.
#   - A child node must NEVER exceed the parent node page range.
#   - If child.end_index > parent.end_index:
#       update the parent end_index accordingly.

# 2. Fix node ordering.
#   - Nodes must appear in ascending page order.
#   - Child nodes must stay inside parent nodes.

# 3. Fix node_id consistency.
#   - Use hierarchical numbering format:
#       0001
#       0001.1
#       0001.2
#       0002
#   - Remove inconsistent formats like:
#       0014-1
#       0014-2

# 4. Preserve hierarchy correctly.

# 5. Preserve summaries and titles.

# 6. Ensure:
#   start_index <= end_index

# 7. Remove duplicate nodes if present.

# 8. Ensure sibling nodes are correctly ordered.

# 9. Ensure parent page ranges fully contain all children.

# 10. Do NOT hallucinate new sections.

# 11. Do NOT remove valid sections.

# OUTPUT RULES:
# - Return valid JSON only.
# - Do NOT explain anything.
# - Do NOT use markdown.
# - Do NOT wrap output in ```json.

# TREE:

# {tree_json}
# """

#     return prompt

# import json
# from open_ai_llm import generate_response
# def refine_tree(tree):

#     prompt = generate_tree_refinement_prompt(
#         json.dumps(tree, ensure_ascii=False, indent=2)
#     )

#     refined_response = generate_response(prompt)
#     print(f"refined response: {refined_response}")

#     refined_tree = json.loads(refined_response)

#     return refined_tree

# tree = [
#   {
#     "node_id": "0001",
#     "title": "About the Federal Reserve",
#     "start_index": 5,
#     "end_index": 5,
#     "summary": "Provides background on the creation, purpose, and structure of the Federal Reserve System, including its 12 districts and where to find more information online.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0002",
#     "title": "1 Overview",
#     "start_index": 7,
#     "end_index": 8,
#     "summary": "Introduces the report’s scope, outlining the five functional areas covered: monetary policy, financial stability, supervision and regulation, payment systems, and consumer and community affairs.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0003",
#     "title": "2 Monetary Policy and Economic Developments",
#     "start_index": 9,
#     "end_index": 15,
#     "summary": "Reviews the Federal Reserve’s monetary policy actions in 2023, including interest‑rate decisions, balance‑sheet runoff, and inflation and labor‑market trends, with summaries of the March 2024 and June 2023 Monetary Policy Reports.",
#     "sub_nodes": [
#       {
#         "node_id": "0004",
#         "title": "March 2024 Summary",
#         "start_index": 9,
#         "end_index": 11,
#         "summary": "Describes the continued easing of inflation, tight labor market, and the FOMC’s view that the policy rate is near its peak while maintaining a restrictive stance.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0005",
#         "title": "June 2023 Summary",
#         "start_index": 15,
#         "end_index": 15,
#         "summary": "Notes inflation still above target, a very tight labor market, modest GDP growth, and further interest‑rate hikes and balance‑sheet reductions by the FOMC.",
#         "sub_nodes": []
#       }
#     ]
#   },
#   {
#     "node_id": "0006",
#     "title": "3 Financial Stability",
#     "start_index": 21,
#     "end_index": 30,
#     "summary": "Details the Board’s monitoring of financial‑system vulnerabilities, international coordination, and activities to promote resilience, including asset‑valuation pressures, leverage, and funding risks.",
#     "sub_nodes": [
#       {
#         "node_id": "0007",
#         "title": "Monitoring Financial Vulnerabilities",
#         "start_index": 22,
#         "end_index": 24,
#         "summary": "Presents the quarterly assessment of four key vulnerabilities—asset valuations, borrowing by households and businesses, financial‑sector leverage, and funding risk.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0008",
#         "title": "Domestic and International Cooperation and Coordination",
#         "start_index": 28,
#         "end_index": 30,
#         "summary": "Describes the Board’s collaboration with the FSOC, Treasury, and the Financial Stability Board on systemic‑risk monitoring, climate‑related risks, and digital‑asset oversight.",
#         "sub_nodes": []
#       }
#     ]
#   },
#   {
#     "node_id": "0009",
#     "title": "4 Supervision and Regulation",
#     "start_index": 31,
#     "end_index": 41,
#     "summary": "Covers the Board’s supervisory framework, the institutions it oversees, examination activities, and specialized exams, including stress testing, cyber‑risk, and novel‑activities supervision.",
#     "sub_nodes": [
#       {
#         "node_id": "0010",
#         "title": "Supervised and Regulated Institutions",
#         "start_index": 32,
#         "end_index": 34,
#         "summary": "Provides tables and descriptions of the categories of banks, holding companies, and other entities subject to Federal Reserve supervision.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0011",
#         "title": "Supervisory Developments",
#         "start_index": 35,
#         "end_index": 39,
#         "summary": "Discusses responses to the SVB and Signature Bank failures, enhancements to supervisory processes, and the focus on risk‑focused examinations.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0012",
#         "title": "Specialized Examinations",
#         "start_index": 37,
#         "end_index": 40,
#         "summary": "Outlines examinations of stress testing, fiduciary activities, IT and cyber risk, government securities, and other specialized areas.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0013",
#         "title": "Enforcement Actions and Climate‑Related Financial Risks",
#         "start_index": 41,
#         "end_index": 41,
#         "summary": "Summarizes the Board’s enforcement authority, recent enforcement actions, and the launch of climate‑scenario analysis and related supervisory principles.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0014",
#         "title": "Enforcement Actions and Financial Disclosures",
#         "start_index": 42,
#         "end_index": 43,
#         "summary": "Details formal and informal enforcement actions taken in 2023, civil money penalties, and financial disclosure requirements for state member banks.",
#         "sub_nodes": [
#           {
#             "node_id": "0014-1",
#             "title": "Formal Enforcement Actions",
#             "start_index": 42,
#             "end_index": 42,
#             "summary": "The Board completed 63 formal enforcement actions in 2023, assessing $542.3 million in civil money penalties, which are remitted to the Treasury or FEMA.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0014-2",
#             "title": "Informal Enforcement Actions",
#             "start_index": 42,
#             "end_index": 42,
#             "summary": "Reserve Banks executed 99 informal actions, including memoranda of understanding, commitment letters, supervisory letters, and board resolutions.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0014-3",
#             "title": "Financial Disclosures by State Member Banks",
#             "start_index": 42,
#             "end_index": 43,
#             "summary": "One state member bank submitted required financial data under Regulation H and the Securities Exchange Act; the data are used for shareholder disclosure.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0014-4",
#             "title": "Internal Appeals of Material Supervisory Determinations",
#             "start_index": 43,
#             "end_index": 43,
#             "summary": "Describes the two‑level independent review process for MSD appeals, including initial review panels and final senior‑Board panels.",
#             "sub_nodes": []
#           }
#         ]
#       },
#       {
#         "node_id": "0015",
#         "title": "Assessments for Supervision and Regulation",
#         "start_index": 43,
#         "end_index": 44,
#         "summary": "Explains assessments levied on large BHCs, SLHCs and designated non‑bank financial companies, and reports the $771 million transferred to the Treasury in 2023.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0016",
#         "title": "Training and Technical Assistance",
#         "start_index": 44,
#         "end_index": 45,
#         "summary": "Covers the Federal Reserve’s provision of training to foreign supervisors, minority‑owned depository institutions, and related outreach programs.",
#         "sub_nodes": [
#           {
#             "node_id": "0016-1",
#             "title": "International Training and Technical Assistance",
#             "start_index": 44,
#             "end_index": 44,
#             "summary": "Organized 20 training seminars for foreign central banks and supervisors, with roughly 900 participants, and partnered with IMF and World Bank on two events.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0016-2",
#             "title": "Efforts to Support Minority‑Owned Depository Institutions",
#             "start_index": 44,
#             "end_index": 45,
#             "summary": "Describes the Partnership for Progress program, MDIs outreach, conferences, and the 16‑institution MDI portfolio at year‑end 2023.",
#             "sub_nodes": []
#           }
#         ]
#       },
#       {
#         "node_id": "0017",
#         "title": "International Engagement and Coordination",
#         "start_index": 45,
#         "end_index": 49,
#         "summary": "Summarizes participation in the Financial Stability Board, Basel Committee, CPMI, and IAIS, including publications and collaborative training events.",
#         "sub_nodes": [
#           {
#             "node_id": "0017-1",
#             "title": "Financial Stability Board Activities",
#             "start_index": 45,
#             "end_index": 46,
#             "summary": "Detailing FSB work on cross‑border payments, crypto‑asset supervision, open‑ended fund vulnerabilities, and third‑party risk toolkits.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0017-2",
#             "title": "Basel Committee on Banking Supervision Contributions",
#             "start_index": 46,
#             "end_index": 46,
#             "summary": "Highlights BCBS involvement in Basel III implementation, banking turmoil review, digital finance, and climate‑risk guidance.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0017-3",
#             "title": "Committee on Payments and Market Infrastructures (CPMI)",
#             "start_index": 47,
#             "end_index": 48,
#             "summary": "Covers CPMI participation, joint publications on cross‑border payments, stablecoins, and collaborative work with IOSCO.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0017-4",
#             "title": "International Association of Insurance Supervisors (IAIS)",
#             "start_index": 48,
#             "end_index": 49,
#             "summary": "Notes IAIS work on insurance capital standards, aggregation method criteria, and climate‑risk guidance, and the role of the IPAC.",
#             "sub_nodes": []
#           }
#         ]
#       },
#       {
#         "node_id": "0018",
#         "title": "Regulatory Developments",
#         "start_index": 55,
#         "end_index": 57,
#         "summary": "Lists 2023 rulemakings, guidance, and policy statements issued jointly or by the Board, covering crypto‑asset risks, liquidity, capital requirements, and climate‑related risk management.",
#         "sub_nodes": [
#           {
#             "node_id": "0018-1",
#             "title": "Rulemakings and Guidance Issued in 2023",
#             "start_index": 55,
#             "end_index": 57,
#             "summary": "Chronological table of agency statements, SR letters, and joint press releases on topics such as crypto‑asset risk, LIBOR transition, third‑party risk, and capital rules.",
#             "sub_nodes": []
#           }
#         ]
#       }
#     ]
#   },
#   {
#     "node_id": "0019",
#     "title": "5 Payment System and Reserve Bank Oversight",
#     "start_index": 68,
#     "end_index": 86,
#     "summary": "Describes the Board’s oversight of Reserve Bank payment‑system services, technology upgrades, facility projects, financial‑statement audits, SOMA holdings, and pro‑forma priced‑services statements for 2023.",
#     "sub_nodes": [
#       {
#         "node_id": "0019-1",
#         "title": "Regulation II Comment Request",
#         "start_index": 68,
#         "end_index": 68,
#         "summary": "In October 2023 the Board sought comments on proposals to lower the maximum debit‑card interchange fee and to set a biennial update process.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0019-2",
#         "title": "Master Account and Services Database",
#         "start_index": 68,
#         "end_index": 68,
#         "summary": "June 2023 launch of a searchable database disclosing entities with access to Reserve Bank master accounts and related services.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0019-3",
#         "title": "Technology Initiatives and Cybersecurity",
#         "start_index": 69,
#         "end_index": 71,
#         "summary": "Implementation of FedNow, multi‑year platform modernizations, cyber‑risk programs, and datacenter upgrades aimed at security, agility, and value.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0019-4",
#         "title": "Facility Renovations",
#         "start_index": 71,
#         "end_index": 71,
#         "summary": "Major multi‑year projects at Philadelphia, Miami, and New York Reserve Banks to replace mechanical, electrical, and vault infrastructure.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0019-5",
#         "title": "Oversight and Audits of Reserve Banks",
#         "start_index": 71,
#         "end_index": 76,
#         "summary": "Annual combined‑statement audits by KPMG, internal‑control reviews using COSO, and Board oversight of financial reporting and controls.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0019-6",
#         "title": "System Open Market Account (SOMA) Review",
#         "start_index": 77,
#         "end_index": 80,
#         "summary": "Board reviews of SOMA holdings, related IT projects, and annual income‑expense tables comparing 2023 with 2022.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0019-7",
#         "title": "Pro Forma Financial Statements for Priced Services",
#         "start_index": 81,
#         "end_index": 85,
#         "summary": "Balance‑sheet and income‑statement pro forma tables for priced services, including assets, liabilities, revenue, imputed costs, and cost‑recovery metrics.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0019-8",
#         "title": "Notes to Priced‑Services Financials",
#         "start_index": 84,
#         "end_index": 85,
#         "summary": "Explanations of short‑term assets, long‑term assets, liability/equity treatment, risk‑management policy, and imputed cost methodology.",
#         "sub_nodes": []
#       }
#     ]
#   },
#   {
#     "node_id": "0020",
#     "title": "6 Consumer and Community Affairs",
#     "start_index": 89,
#     "end_index": 106,
#     "summary": "Covers the Board’s consumer‑protection supervision, CRA performance evaluation, fair‑lending enforcement, mergers oversight, outreach, complaint handling, regulatory updates, and research activities in 2023.",
#     "sub_nodes": [
#       {
#         "node_id": "0020-1",
#         "title": "Program Overview",
#         "start_index": 89,
#         "end_index": 90,
#         "summary": "Describes the Board’s mission to promote fair financial markets, consumer rights, and community development through supervision, regulation, research, and public engagement.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0020-2",
#         "title": "Consumer Compliance Supervision",
#         "start_index": 89,
#         "end_index": 90,
#         "summary": "Supervision of state member banks for compliance with TILA, EFTA, ECOA, FHA, UDAP, and CRA, including policy development and examination guidance.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0020-3",
#         "title": "Community Reinvestment Act (CRA) Performance",
#         "start_index": 92,
#         "end_index": 92,
#         "summary": "2023 CRA examinations of 174 state member banks; rating outcomes and the final rule issued in October 2023 to modernize CRA regulations.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0020-4",
#         "title": "Fair Lending and UDAP Enforcement",
#         "start_index": 93,
#         "end_index": 94,
#         "summary": "Enforcement actions, referral of one fair‑lending matter to DOJ, and use of informal supervisory tools to correct violations.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0020-5",
#         "title": "Mergers and Acquisitions Review",
#         "start_index": 95,
#         "end_index": 95,
#         "summary": "Board’s statutory considerations for M&A, reliance on CRA performance and fair‑lending results, and coordination of pre‑membership examinations.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0020-6",
#         "title": "Outreach, Training, and Examiner Development",
#         "start_index": 96,
#         "end_index": 99,
#         "summary": "Consumer‑compliance webinars, Fair Lending Interagency Webinar, examiner training programs, rapid‑response sessions, and CPD offerings.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0020-7",
#         "title": "Consumer Complaints and Inquiries",
#         "start_index": 100,
#         "end_index": 100,
#         "summary": "Table 6.1 shows complaint volumes by product; 95 % of 6,115 complaints were closed, with breakdown of issues and resolutions.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0020-8",
#         "title": "Regulatory Indexing and Threshold Updates",
#         "start_index": 101,
#         "end_index": 102,
#         "summary": "Annual adjustments to exemption thresholds in Regulation Z, Regulation M, higher‑priced mortgage appraisal limits, and CRA asset‑size thresholds.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0020-9",
#         "title": "Research, Surveys, and Publications",
#         "start_index": 103,
#         "end_index": 105,
#         "summary": "2023 SHED survey results, consumer‑community context articles, working papers, and the Community Development Research Seminar Series on housing markets.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0020-10",
#         "title": "Community Development Initiatives",
#         "start_index": 106,
#         "end_index": 106,
#         "summary": "Efforts to understand post‑pandemic labor market impacts, support for minority‑depository institutions, and outreach through the Community Advisory Council.",
#         "sub_nodes": []
#       }
#     ]
#   },
#   {
#     "node_id": "0021",
#     "title": "Appendixes",
#     "start_index": 107,
#     "end_index": 110,
#     "summary": "Lists supplemental material, including the Federal Reserve System organization chart and staff directories for Board divisions and agencies.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0022",
#     "title": "Division of Research and Statistics Leadership",
#     "start_index": 112,
#     "end_index": 112,
#     "summary": "Lists directors, associate directors, senior associate directors and other leadership positions within the Division of Research and Statistics.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0023",
#     "title": "Federal Reserve System Organization – Board and Districts",
#     "start_index": 113,
#     "end_index": 140,
#     "summary": "Provides extensive listings of board members, division heads, Reserve Bank leadership, and district directors across the Federal Reserve System.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0024",
#     "title": "Federal Open Market Committee",
#     "start_index": 117,
#     "end_index": 117,
#     "summary": "Details the composition of the FOMC, its members, and alternate members for 2023, including meeting frequency and references to minutes.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0025",
#     "title": "Officers (Board Staff)",
#     "start_index": 118,
#     "end_index": 119,
#     "summary": "Lists senior officers such as the Secretary, Deputy Secretary, economists, and general counsel with their appointment dates.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0026",
#     "title": "Board of Governors Advisory Councils",
#     "start_index": 119,
#     "end_index": 119,
#     "summary": "Describes the Federal Advisory Council, its purpose, meeting schedule in 2023, and member representatives from each Federal Reserve District.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0027",
#     "title": "Community Depository Institutions Advisory Council",
#     "start_index": 120,
#     "end_index": 120,
#     "summary": "Outlines the council’s role advising the Board on community depository institutions, its membership composition, and 2023 meeting dates.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0028",
#     "title": "Community Advisory Council",
#     "start_index": 121,
#     "end_index": 121,
#     "summary": "Provides background on the council’s formation, mission to represent low‑ and moderate‑income interests, and 2023 meeting schedule.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0029",
#     "title": "Model Validation Council",
#     "start_index": 122,
#     "end_index": 122,
#     "summary": "Explains the council’s purpose of advising on stress‑test model assessment; notes that it had no members or meetings in 2023.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0030",
#     "title": "Reserve Bank and Branch Leadership",
#     "start_index": 141,
#     "end_index": 143,
#     "summary": "Lists chairs, deputy chairs, presidents and first vice‑presidents of each Reserve Bank and selected branches for 2023.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0031",
#     "title": "Leadership Conferences",
#     "start_index": 144,
#     "end_index": 144,
#     "summary": "Describes the Conference of Chairs and Conference of Presidents, their 2023 meeting dates, and the executive committee members.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0032",
#     "title": "Conference of First Vice Presidents",
#     "start_index": 145,
#     "end_index": 145,
#     "summary": "Details the 2023 officers of the Conference of First Vice Presidents and notes election outcomes for 2024.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0033",
#     "title": "FOMC Meeting Minutes Appendix",
#     "start_index": 147,
#     "end_index": 148,
#     "summary": "Provides URLs and brief descriptions for the eight regularly scheduled FOMC meeting minutes released in 2023.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0034",
#     "title": "Federal Reserve System Audits",
#     "start_index": 149,
#     "end_index": 152,
#     "summary": "Summarizes audit responsibilities, OIG activities, GAO reports, and highlights of 2023 audit findings and investigations.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0035",
#     "title": "Federal Reserve System Budgets",
#     "start_index": 153,
#     "end_index": 153,
#     "summary": "Presents 2023 budget performance and 2024 outlook, including operating expenses, employment, and capital expenditures across the System.",
#     "sub_nodes": [
#       {
#         "node_id": "0036",
#         "title": "7 Budgets",
#         "start_index": 154,
#         "end_index": 166,
#         "summary": "Comprehensive overview of the System’s 2023 financial statements and 2024 budget projections, covering operating expenses, revenue, employment, and capital allocations.",
#         "sub_nodes": [
#           {
#             "node_id": "0036-1",
#             "title": "Operating Expenses and Revenue",
#             "start_index": 154,
#             "end_index": 155,
#             "summary": "Table D.1 details total system operating expenses, revenue from priced services, and net expenses after reimbursable claims, highlighting modest variances from the 2024 budget.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0036-2",
#             "title": "Employment",
#             "start_index": 155,
#             "end_index": 167,
#             "summary": "Tables D.2 and D.11 present full‑time‑equivalent employment across the Board, OIG, and Reserve Banks, showing slight FTE declines in 2023 and modest projected growth for 2024.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0036-3",
#             "title": "Capital Budgets Overview",
#             "start_index": 157,
#             "end_index": 168,
#             "summary": "Discussion of 2024 capital budgets for the Board and Reserve Banks, including single‑year and multiyear expenditures, strategic project funding, and FY2024 capital totals.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0036-4",
#             "title": "Currency Budget Details",
#             "start_index": 169,
#             "end_index": 174,
#             "summary": "Breakdown of the Board’s currency budget, BEP single‑cycle costs, board‑level expenses, and multicycle project funding supporting note production and security enhancements.",
#             "sub_nodes": []
#           }
#         ]
#       },
#       {
#         "node_id": "0037",
#         "title": "8 Record of Policy Actions",
#         "start_index": 175,
#         "end_index": 182,
#         "summary": "Appendix enumerating 2023 Board policy actions, including new regulations, policy statements, climate‑risk guidance, and interest‑rate decisions for reserve balances.",
#         "sub_nodes": [
#           {
#             "node_id": "0037-1",
#             "title": "Regulations and Rulemakings",
#             "start_index": 175,
#             "end_index": 176,
#             "summary": "Final rules adopting risk‑based capital standards (Reg Q) and modernizing the Community Reinvestment Act (Reg BB) with joint FDIC and OCC participation.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0037-2",
#             "title": "Policy Statements and Guidance",
#             "start_index": 177,
#             "end_index": 179,
#             "summary": "Interagency statements on credit‑loss allowances, commercial real‑estate loan accommodations, Section 9(13) of the Federal Reserve Act, climate‑related risk management, and third‑party risk.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0037-3",
#             "title": "Interest on Reserve Balances",
#             "start_index": 180,
#             "end_index": 181,
#             "summary": "Chronology of Board actions raising the interest rate on reserve balances throughout 2023 to support FOMC target‑range adjustments.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0037-4",
#             "title": "Discount Rates for Depository Institutions",
#             "start_index": 182,
#             "end_index": 182,
#             "summary": "Table E.1 summarises primary, secondary, and seasonal credit rates at year‑end 2023 and notes the Board’s approvals of rate changes during the year.",
#             "sub_nodes": []
#           },
#           {
#             "node_id": "0037-5",
#             "title": "Primary Credit Rate Adjustments 2023",
#             "start_index": 183,
#             "end_index": 183,
#             "summary": "Details the Board’s approvals to raise the primary credit rate from 4½% to 5½% in four FOMC meetings during 2023, including voting members.",
#             "sub_nodes": []
#           }
#         ]
#       }
#     ]
#   },
#   {
#     "node_id": "0038",
#     "title": "Government Performance and Results Act (GPRA) Overview",
#     "start_index": 184,
#     "end_index": 184,
#     "summary": "Explains the Board’s voluntary compliance with GPRA, describing its 2020–23 Strategic Plan, Annual Performance Plans, and Annual Performance Reports.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0039",
#     "title": "Litigation",
#     "start_index": 185,
#     "end_index": 186,
#     "summary": "Summarizes lawsuits and appeals involving the Board in 2023, listing pending and resolved cases, many relating to Freedom of Information Act and Regulation II challenges.",
#     "sub_nodes": []
#   },
#   {
#     "node_id": "0040",
#     "title": "Statistical Tables",
#     "start_index": 187,
#     "end_index": 203,
#     "summary": "Appendix G containing a series of statistical tables on open market operations, holdings, reserve requirements, banking offices, reserves, and other key monetary statistics.",
#     "sub_nodes": [
#       {
#         "node_id": "0040-1",
#         "title": "Table G.1 – Federal Reserve open market transactions, 2023",
#         "start_index": 187,
#         "end_index": 188,
#         "summary": "Monthly totals of purchases, sales, exchanges and redemptions of U.S. Treasury securities, agency securities and other maturities for 2023.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0040-2",
#         "title": "Table G.2 – Federal Reserve Bank holdings of U.S. Treasury and federal agency securities, 2021‑23",
#         "start_index": 189,
#         "end_index": 190,
#         "summary": "Year‑end holdings by maturity and issuer, showing declines in Treasury securities and stable holdings of agency securities.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0040-3",
#         "title": "Table G.3 – Reserve requirements of depository institutions, 2023",
#         "start_index": 191,
#         "end_index": 191,
#         "summary": "Shows that net transaction accounts, nonpersonal time deposits and eurocurrency liabilities had a 0% reserve requirement as of year‑end 2023.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0040-4",
#         "title": "Table G.4 – Banking offices and banks affiliated with bank holding companies, 2022‑23",
#         "start_index": 192,
#         "end_index": 192,
#         "summary": "Counts of commercial banks, branches and affiliated banks, highlighting modest declines in total offices between 2022 and 2023.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0040-5",
#         "title": "Table G.5A – Reserves of depository institutions, Federal Reserve Bank credit, and related items, year‑end 1984‑2023 and month‑end 2023",
#         "start_index": 193,
#         "end_index": 196,
#         "summary": "Long‑term series of reserve fund sources, credit extensions and assets, with detailed monthly breakdowns for 2023.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0040-6",
#         "title": "Table G.5B – Reserves of depository institutions, year‑end 1918‑1983",
#         "start_index": 197,
#         "end_index": 200,
#         "summary": "Historical reserve data covering 1918‑1983, including factors supplying and absorbing reserve funds.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0040-7",
#         "title": "Table G.6 – Principal assets and liabilities of insured commercial banks, June 30, 2022‑23",
#         "start_index": 201,
#         "end_index": 201,
#         "summary": "Balance‑sheet totals for member and non‑member banks, showing slight shifts in loans, investments and deposits between 2022 and 2023.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0040-8",
#         "title": "Table G.7 – Initial margin requirements under Regulations T, U, and X",
#         "start_index": 202,
#         "end_index": 202,
#         "summary": "Historical percentages of market value required as margin for short sales, stocks and convertible bonds from 1934 to 1974.",
#         "sub_nodes": []
#       },
#       {
#         "node_id": "0040-9",
#         "title": "Table G.8A – Statement of condition of the Federal Reserve Banks, December 31, 2022‑23",
#         "start_index": 203,
#         "end_index": 203,
#         "summary": "Assets and liabilities of each Reserve Bank, highlighting declines in loans and securities and an increase in deferred assets to the Treasury.",
#         "sub_nodes": []
#       }
#     ]
#   }
# ]

# refined_tree = refine_tree(tree)
# print(refined_tree)
# from extract_pages import save_pages_to_json
# save_pages_to_json(refined_tree, "json_files/tree1.json")