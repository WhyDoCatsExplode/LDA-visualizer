# Export a fitted topicmodels LDA for the LDA topic modelling toolkit.
# Run after fitting (lda_model = your LDA() result, document_dfm = the dfm it was fit on,
# document_list = the raw lines per file), then use "Import model" in the page and pick
# the JSON. Drop `texts` to keep the file small; you can then select the .txt
# files alongside the JSON to get the per-word document view back.

library(jsonlite)

post <- posterior(lda_model)

write_json(list(
  format = "lda-toolkit", version = 1, source = "R · topicmodels",
  terms  = colnames(post$terms),
  phi    = unname(post$terms),       # K × V: p(w | z), β in the article
  docs   = rownames(post$topics),    # file names, e.g. "1977.txt"
  theta  = unname(post$topics),      # D × K: topic mixtures (θ)
  tokens = unname(ntoken(document_dfm)),
  texts  = unname(sapply(document_list, paste, collapse = "\n"))
), "lda_model.json", auto_unbox = TRUE, digits = I(6))
