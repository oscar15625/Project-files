# PT metric dictionary

Evidence class: REPRODUCED_MECHANISM. November source states, V5 node/node Sioux states; no substitution of October v6 data.

| Field | Definition and unit | Limitation |
|---|---|---|
| initial_pt | Expected flow on gate-to-PT access links, by sales channel | Not proof of a PT vehicle ride |
| pt_vehicle_link_traversals | Flow summed over edges with same PT line at both ends | Passenger-link count, not unique persons |
| pt_paid_links | Non-MaaS retail/PT or MaaS wholesale/PT attributes times flow | Equals PT ride links only in this link-priced specialization |
| pt_boarding_events | Entries from gates or another service/line into PT state | Repeated entries count; a ride need not follow |
| pt_pt_transfers | Cross-line PT state transitions | Not PT-MoD transfer count |
| any_actual_pt_trips | Demand weighted probability of at least one PT ride edge | Absorbing-chain event probability, not access-flow proxy |
| actual_mod_and_pt_trips | Probability of both MoD road and PT ride edges, inclusion-exclusion | Expected mixed-mode trips, no realized individual trajectories |
| initial_pt_but_no_pt_ride | PT initial access followed by no PT ride edge | Quantifies access-only misclassification |
| pt_passenger_distance_model_units | Ride-link flow times reconstructed lengths | Not verified passenger-km; Sioux uses V5 proxy lengths |

The event calculation uses an absorbing Markov kernel recovered from positive gate injections. Removing event transitions gives avoidance probability via a linear system; inclusion-exclusion yields the both-mode event. Probability and accounting identities are independently checked. Non-MaaS supports multimodal travel; a change of channel is not automatically a physical-mode change.

Paper Table 2 PT-share sums remain 25.5% and Table 3 changes 10.6% to 28.6%. These rounded aggregate labels do not assert unchanged PT flow on every link or OD. Figure 6 / section 5.1.3 explicitly describes local OD(1,5) PT growth. Mapping those shares to this code's first-access metric remains unresolved.
