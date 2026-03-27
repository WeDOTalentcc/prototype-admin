# Geração de Datasets WSI

## Geração Automática de 19.500 Exemplos

### Executar:

```bash
cd lia-agent-system
python -m training.data_generation.generate_wsi_datasets
```

### Output:

```
lia-agent-system/training/datasets/synthetic/
├── questions_5000.json (5.000 perguntas científicas)
├── responses_10000.json (10.000 respostas calibradas)
├── red_flags_1000.json (1.000 red flags)
├── reports_2000.json (2.000 pareceres)
├── feedbacks_1500.json (1.500 feedbacks)
└── metadata.json
```

### Tempo Estimado:
- 5.000 perguntas: ~3 horas
- 10.000 respostas: ~6 horas
- 1.000 red flags: ~1 hora
- 2.000 pareceres: ~2 horas
- 1.500 feedbacks: ~1.5 horas

**Total: ~14 horas** (pode rodar overnight)

### Custo Estimado:
- ~19.500 requests × $0.015/request = **~$300**
- Conversão: **~R$ 1.700**

### Pós-Geração:

Após gerar os 19.500 exemplos sintéticos, **5 experts anotarão 2.000 exemplos críticos** manualmente para garantir máxima qualidade nos casos mais importantes.

**Total final: 21.500 exemplos** (19.5K sintéticos + 2K humanos)
