from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

from app.config import settings
from app.services.classifier import SpeciesResult
from app.services.safety_data import get_lookalike, get_protection

SafetyVerdict = Literal["safe", "caution", "danger"]

logger = logging.getLogger(__name__)

# Messages                                                                               
NO_RESULT_MESSAGE = (
    "Couldn't identify. Please reshoot with clearer details."
)                                                       
                                          
UNCERTAIN_MESSAGE = (
    "Low confidence ID. Dangerous to consume. Seek expert advice."
)                                       
                                                                                           
POSSIBLE_MATCH_MESSAGE = (
    "Multiple species detected. Verify with a field guide before use."
)

@dataclass
class CandidateSafety:
    species: str
    confidence: float
    safety_verdict: SafetyVerdict
    warning_message: str | None = None


@dataclass
class SafetyStaticResult:
    confidence_tier: Literal["strong_match", "possible_match", "uncertain", "no_result"] = "uncertain"                               
    candidates: list[CandidateSafety] = field(default_factory=list)
    lookalike_findings: list[dict] = field(default_factory=list)
    protection_findings: list[dict] = field(default_factory=list)
    safety_info: dict = field(default_factory=dict)
    safety_verdict: SafetyVerdict = "caution"
    warning_message: str | None = None


def _determine_tier(top_confidence: float, confidence_ratio: float, result: SafetyStaticResult) -> str:
    
    if top_confidence < settings.cv_confidence_floor:
        result.safety_verdict = "danger"
        result.warning_message = NO_RESULT_MESSAGE
        return "no_result"

    if top_confidence >= settings.cv_confidence_strong and confidence_ratio >= settings.cv_ratio_strong:               
        return "strong_match"
    elif confidence_ratio < settings.cv_ratio_possible or top_confidence < settings.cv_confidence_uncertain:           
       return "uncertain"                                                 
           
    return "possible_match" 


def _candidate_safety(species, predictions, result):

    if result.confidence_tier == "strong_match":

        entry = get_lookalike(species)
        if entry is not None:
            result.lookalike_findings = entry.get("lookalikes", [])
            result.safety_verdict = entry.get("safety_verdict", "caution")
            result.warning_message = entry.get("warnings")
            result.safety_info = {
                "edibility": entry.get("edibility"),
                "edible_parts": entry.get("edible_parts", []),
                "preparation": entry.get("preparation"),
                "sources": entry.get("sources", []),
            }

            edibility = entry.get("edibility", [])
            if isinstance(edibility, str):
                edibility = [edibility]
            if any(e in ("deadly", "toxic") for e in edibility):
                result.safety_verdict = "danger"

    else:                                                                                    
    # build candidate list for top predictions
        worst_verdict = "safe"                                                               
        verdict_rank = {"safe": 0, "caution": 1, "danger": 2}
                                                                                            
        for pred in predictions[:3]:                                                         
            entry = get_lookalike(pred.species)
            verdict = entry.get("safety_verdict", "caution") if entry else "caution"         
                                                
            entry_edibility = entry.get("edibility", []) if entry else []
            if isinstance(entry_edibility, str):
                entry_edibility = [entry_edibility]
            if any(e in ("deadly", "toxic") for e in entry_edibility):
                verdict = "danger"          
            result.candidates.append(CandidateSafety(                                        
                species=pred.species,                                                        
                confidence=pred.confidence,     
                safety_verdict=verdict,     
                warning_message=entry.get("warnings") if entry else None,
            ))                                                                               
    
            if verdict_rank[verdict] > verdict_rank[worst_verdict]:                          
                worst_verdict = verdict     

        if result.confidence_tier == "uncertain":                                            
            result.safety_verdict = "caution" if worst_verdict == "safe" else worst_verdict
            result.warning_message = UNCERTAIN_MESSAGE                                       
        else:                               
            result.safety_verdict = worst_verdict
            result.warning_message = POSSIBLE_MATCH_MESSAGE 


def run_safety_static(
    species_class_name: str,
    predictions: list[SpeciesResult],
    state_abbr: str | None,
) -> SafetyStaticResult:

    result = SafetyStaticResult()

    # confidence gate
    top_confidence = predictions[0].confidence
    confidence_ratio = predictions[0].confidence / predictions[1].confidence if len(predictions) > 1 else float("inf")

    result.confidence_tier = _determine_tier(top_confidence, confidence_ratio, result)

    if result.confidence_tier != "no_result":
        _candidate_safety(species_class_name, predictions, result)
   
    # protection check
    protection_entry = get_protection(species_class_name)
    if protection_entry is not None:
        for restriction in protection_entry["restrictions"]:
            states = [s.lower() for s in restriction["states"]]
            if "all" in states or (state_abbr is not None and state_abbr.lower() in states):
                result.protection_findings.append(restriction)

    return result
