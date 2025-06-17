from collections import defaultdict


def filter_ene_spans(spans):
    """
    Filter spans to keep only the first level ENE spans.
    """
    filtered_spans = []
    for span in spans:
        if span['label'].startswith('ENE-'):
            # Check if there are no other ENE spans that are fully contained within this one
            if not any(s['label'].startswith('ENE-') and s['start'] >= span['start'] and s['end'] <= span['end'] and s != span for s in spans):
                filtered_spans.append(span)
        else:
            filtered_spans.append(span)
    return filtered_spans


def spans_overlap_with_offset(start1, end1, start2, end2, max_offset=1):
    start1, end1, start2, end2 = map(int, (start1, end1, start2, end2))
    return not (end1 <= start2 - max_offset or end2 <= start1 - max_offset)


def deduplicate_entities(entities):
    seen = set()
    unique = []
    for ent in entities:
        key = (int(ent.get("start")), int(ent.get("end")), ent.get("label"))
        if key not in seen:
            seen.add(key)
            unique.append(ent)
    return unique


def evaluate_entity_match_with_offset(gold_docs, pred_docs, gold_label_key="label", pred_label_key="label", max_offset=1):
    type_counts = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0})
    
    matched_by_label = defaultdict(list)
    false_positives_by_label = defaultdict(list)
    false_negatives_by_label = defaultdict(list)

    for gold_entities, pred_entities in zip(gold_docs, pred_docs):
        gold_entities = deduplicate_entities(gold_entities)
        pred_entities = deduplicate_entities(pred_entities)

        gold_matched = set()
        pred_matched = set()

        for i, pred in enumerate(pred_entities):
            pred_start = int(pred["start"])
            pred_end = int(pred["end"])
            pred_label = pred[pred_label_key]

            best_match = None
            for j, gold in enumerate(gold_entities):
                if j in gold_matched:
                    continue
                gold_start = int(gold["start"])
                gold_end = int(gold["end"])
                gold_label = gold[gold_label_key]

                if pred_label != gold_label:
                    continue

                if spans_overlap_with_offset(pred_start, pred_end, gold_start, gold_end, max_offset):
                    best_match = j
                    break

            if best_match is not None:
                gold_matched.add(best_match)
                pred_matched.add(i)
                type_counts[pred_label]["TP"] += 1
                matched_by_label[pred_label].append({
                    "gold": gold_entities[best_match],
                    "pred": pred
                })
            else:
                type_counts[pred_label]["FP"] += 1
                false_positives_by_label[pred_label].append(pred)

        for k, gold in enumerate(gold_entities):
            if k not in gold_matched:
                gold_label = gold[gold_label_key]
                type_counts[gold_label]["FN"] += 1
                false_negatives_by_label[gold_label].append(gold)

    results = {}
    scores = {}
    total_TP = total_FP = total_FN = 0
    precisions, recalls, f1s = [], [], []

    for label, counts in type_counts.items():
        tp = counts["TP"]
        fp = counts["FP"]
        fn = counts["FN"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        scores[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "TP": tp,
            "FP": fp,
            "FN": fn
        }

        total_TP += tp
        total_FP += fp
        total_FN += fn
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

        results[label] = {
            "matched": matched_by_label[label],
            "false_positives": false_positives_by_label[label],
            "false_negatives": false_negatives_by_label[label]
        }

    # Micro-averaged scores
    micro_precision = total_TP / (total_TP + total_FP) if (total_TP + total_FP) > 0 else 0
    micro_recall = total_TP / (total_TP + total_FN) if (total_TP + total_FN) > 0 else 0
    micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0

    # Macro-averaged scores
    macro_precision = sum(precisions) / len(precisions) if precisions else 0
    macro_recall = sum(recalls) / len(recalls) if recalls else 0
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0

    scores["micro_avg"] = {
        "precision": micro_precision,
        "recall": micro_recall,
        "f1": micro_f1,
        "TP": total_TP,
        "FP": total_FP,
        "FN": total_FN
    }

    scores["macro_avg"] = {
        "precision": macro_precision,
        "recall": macro_recall,
        "f1": macro_f1
    }

    return scores, results



if __name__ == "__main__":

    # expected format for gold_docs and pred_docs
    gold_docs = [
        [{"start": 0, "end": 5, "label": "PER"}, {"start": 10, "end": 15, "label": "LOC"}],
        [{"start": 2, "end": 7, "label": "PER"}]
    ]
    pred_docs = [
        [{"start": 0, "end": 5, "label": "PER"}, {"start": 10, "end": 15, "label": "LOC"}],
        [{"start": 2, "end": 7, "label": "PER"}, {"start": 20, "end": 25, "label": "ORG"}]
    ]
    scores, results = evaluate_entity_match_with_offset(gold_docs, pred_docs)
    print("Scores:", scores)
    print("Results:", results)
