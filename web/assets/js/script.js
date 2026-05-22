const EPSILON = "epsilon";
const FIM = "$";

const producoes = {
  1: { esquerda: "S", direita: ["c", "A", "a"] },
  2: { esquerda: "A", direita: ["c", "B"] },
  3: { esquerda: "A", direita: ["B"] },
  4: { esquerda: "B", direita: ["b", "c", "B"] },
  5: { esquerda: "B", direita: [] }
};

const firstFollowResolvido = [
  ["producao", "first", "follow"],
  ["1-S -> cAa", "c", FIM],
  ["2-A -> cB", "c", ""],
  ["3-A -> B", `b, ${EPSILON}`, "a"],
  ["4-B -> bcB", "b", ""],
  ["5-B -> epsilon", EPSILON, "a"]
];

const tabelaParserResolvida = [
  ["tabela parser", "a", "b", "c", EPSILON, FIM],
  ["S", "", "", "1", "", ""],
  ["A", "3 (follow)", "3", "2", "3 (didatico)", ""],
  ["B", "5 (follow)", "4", "", "5 (didatico)", ""]
];

const pilhaResolvida = [
  ["pilha", "c", "b", "c", "a", "", ""],
  ["", "", "b", "", "", "", ""],
  ["c", "", "c", "c", "", "", ""],
  ["A", "A", "B", "B", "B pq tem epsilon", "", ""],
  ["a", "a", "a", "a", "a", "a", ""],
  [FIM, FIM, FIM, FIM, FIM, FIM, "terminou de esvaziar a pilha"],
  ["c,c", "A,a", "b,b", "c,c", "B,a", "a,a", ""]
];

const tabelaAnalise = {
  "S|c": 1,
  "A|c": 2,
  "A|b": 3,
  "A|a": 3,
  "B|b": 4,
  "B|a": 5
};

const terminais = new Set(["a", "b", "c", FIM]);
const naoTerminais = new Set(["S", "A", "B"]);

const form = document.querySelector("#sentence-form");
const input = document.querySelector("#sentence-input");
const exampleButton = document.querySelector("#example-button");
const resultTitle = document.querySelector("#result-title");
const resultBadge = document.querySelector("#result-badge");
const summaryStrip = document.querySelector("#summary-strip");
const derivationRibbon = document.querySelector("#derivation-ribbon");

function formatarProducao(numero) {
  const producao = producoes[numero];
  const direita = producao.direita.length ? producao.direita.join("") : EPSILON;
  return `${producao.esquerda} -> ${direita}`;
}

function textoDaPilha(pilha) {
  return [...pilha].reverse().join("");
}

function textoDaEntrada(entrada, posicao) {
  return entrada.slice(posicao).join("");
}

function prepararEntrada(sentenca) {
  let texto = sentenca.replace(/\s+/g, "").toLowerCase();

  if (texto.endsWith(FIM)) {
    texto = texto.slice(0, -1);
  }

  for (const simbolo of texto) {
    if (!["a", "b", "c"].includes(simbolo)) {
      throw new Error(`Simbolo invalido na entrada: ${simbolo}`);
    }
  }

  return [...texto, FIM];
}

function analisar(sentenca) {
  let entrada;

  try {
    entrada = prepararEntrada(sentenca);
  } catch (erro) {
    return {
      aceita: false,
      entradaNormalizada: sentenca,
      passos: [],
      derivacao: ["S"],
      celulasUsadas: new Set(),
      erro: erro.message
    };
  }

  const pilha = [FIM, "S"];
  const passos = [];
  const derivacao = ["S"];
  const celulasUsadas = new Set();
  let sentencial = ["S"];
  let posicao = 0;
  let passo = 1;

  while (pilha.length) {
    const topo = pilha[pilha.length - 1];
    const simbolo = entrada[posicao];

    if (topo === FIM && simbolo === FIM) {
      return {
        aceita: true,
        entradaNormalizada: entrada.join(""),
        passos,
        derivacao,
        celulasUsadas,
        erro: ""
      };
    }

    if (terminais.has(topo)) {
      if (topo !== simbolo) {
        passos.push({
          numero: passo,
          pilha: textoDaPilha(pilha),
          entrada: textoDaEntrada(entrada, posicao),
          acao: `Erro: esperado ${topo}, encontrado ${simbolo}`,
          erro: true
        });

        return {
          aceita: false,
          entradaNormalizada: entrada.join(""),
          passos,
          derivacao,
          celulasUsadas,
          erro: `Esperado ${topo}, encontrado ${simbolo}.`
        };
      }

      passos.push({
        numero: passo,
        pilha: textoDaPilha(pilha),
        entrada: textoDaEntrada(entrada, posicao),
        acao: `Consome ${topo}`,
        producao: ""
      });

      pilha.pop();
      posicao += 1;
      passo += 1;
      continue;
    }

    if (naoTerminais.has(topo)) {
      const chave = `${topo}|${simbolo}`;
      const numeroProducao = tabelaAnalise[chave];

      if (!numeroProducao) {
        passos.push({
          numero: passo,
          pilha: textoDaPilha(pilha),
          entrada: textoDaEntrada(entrada, posicao),
          acao: `Erro: nao existe M(${topo}, ${simbolo})`,
          erro: true
        });

        return {
          aceita: false,
          entradaNormalizada: entrada.join(""),
          passos,
          derivacao,
          celulasUsadas,
          erro: `Nao existe M(${topo}, ${simbolo}).`
        };
      }

      celulasUsadas.add(chave);
      passos.push({
        numero: passo,
        pilha: textoDaPilha(pilha),
        entrada: textoDaEntrada(entrada, posicao),
        acao: `Usa ${numeroProducao}: ${formatarProducao(numeroProducao)}`,
        producao: numeroProducao
      });

      pilha.pop();
      const direita = producoes[numeroProducao].direita;

      for (let i = direita.length - 1; i >= 0; i -= 1) {
        pilha.push(direita[i]);
      }

      const indice = sentencial.findIndex((simboloAtual) => simboloAtual === topo);
      if (indice !== -1) {
        sentencial.splice(indice, 1, ...direita);
        derivacao.push(sentencial.length ? sentencial.join("") : EPSILON);
      }

      passo += 1;
      continue;
    }

    return {
      aceita: false,
      entradaNormalizada: entrada.join(""),
      passos,
      derivacao,
      celulasUsadas,
      erro: `Simbolo desconhecido ${topo}.`
    };
  }

  return {
    aceita: false,
    entradaNormalizada: entrada.join(""),
    passos,
    derivacao,
    celulasUsadas,
    erro: "Pilha vazia antes do fim da entrada."
  };
}

function criarCelula(tag, texto, className = "") {
  const cell = document.createElement(tag);
  cell.textContent = texto || "";
  if (className) {
    cell.className = className;
  }
  return cell;
}

function renderizarTabelaSimples(id, linhas, opcoes = {}) {
  const tabela = document.querySelector(id);
  tabela.innerHTML = "";

  const thead = document.createElement("thead");
  const trHead = document.createElement("tr");
  linhas[0].forEach((texto, indice) => {
    trHead.appendChild(criarCelula("th", texto || (opcoes.cabecalhoVazio ?? ""), indice === 0 ? "code-cell" : ""));
  });
  thead.appendChild(trHead);
  tabela.appendChild(thead);

  const tbody = document.createElement("tbody");
  linhas.slice(1).forEach((linha) => {
    const tr = document.createElement("tr");
    linha.forEach((texto, indice) => {
      const tag = indice === 0 ? "th" : "td";
      const classes = ["code-cell"];
      if (!texto) {
        classes.push("empty-cell");
      }
      if (String(texto).includes("didatico") || String(texto).includes("follow")) {
        classes.push("didactic-cell");
      }
      tr.appendChild(criarCelula(tag, texto, classes.join(" ")));
    });
    tbody.appendChild(tr);
  });
  tabela.appendChild(tbody);
}

function renderizarParser(celulasUsadas) {
  const tabela = document.querySelector("#parser-table");
  tabela.innerHTML = "";
  const cabecalho = tabelaParserResolvida[0];
  const thead = document.createElement("thead");
  const trHead = document.createElement("tr");
  cabecalho.forEach((texto, indice) => trHead.appendChild(criarCelula("th", texto, indice === 0 ? "code-cell" : "")));
  thead.appendChild(trHead);
  tabela.appendChild(thead);

  const tbody = document.createElement("tbody");
  tabelaParserResolvida.slice(1).forEach((linha) => {
    const naoTerminal = linha[0];
    const tr = document.createElement("tr");
    linha.forEach((texto, indice) => {
      const tag = indice === 0 ? "th" : "td";
      const classes = ["code-cell"];
      const terminal = cabecalho[indice];

      if (!texto) {
        classes.push("empty-cell");
      }

      if (String(texto).includes("didatico") || String(texto).includes("follow")) {
        classes.push("didactic-cell");
      }

      if (indice > 0 && celulasUsadas.has(`${naoTerminal}|${terminal}`)) {
        classes.push("used-cell");
      }

      tr.appendChild(criarCelula(tag, texto, classes.join(" ")));
    });
    tbody.appendChild(tr);
  });
  tabela.appendChild(tbody);
}

function renderizarProducoes() {
  const container = document.querySelector("#productions");
  container.innerHTML = "";

  Object.keys(producoes).forEach((numero) => {
    const linha = document.createElement("div");
    linha.className = "production-row";

    const indice = document.createElement("span");
    indice.className = "production-number";
    indice.textContent = numero;

    const texto = document.createElement("span");
    texto.className = "production-text";
    texto.textContent = formatarProducao(numero);

    linha.append(indice, texto);
    container.appendChild(linha);
  });
}

function renderizarResumo(resultado) {
  const resumo = [
    ["Entrada", resultado.entradaNormalizada || "(vazia)"],
    ["Passos", String(resultado.passos.length)],
    ["Erro", resultado.erro || "nenhum"]
  ];

  summaryStrip.innerHTML = "";
  resumo.forEach(([rotulo, valor]) => {
    const item = document.createElement("div");
    item.className = "summary-item";

    const label = document.createElement("div");
    label.className = "summary-label";
    label.textContent = rotulo;

    const value = document.createElement("div");
    value.className = "summary-value";
    value.textContent = valor;

    item.append(label, value);
    summaryStrip.appendChild(item);
  });
}

function renderizarDerivacao(resultado) {
  derivationRibbon.innerHTML = "";

  resultado.derivacao.forEach((forma, indice) => {
    const chip = document.createElement("span");
    chip.className = "derivation-chip";
    chip.textContent = forma;
    derivationRibbon.appendChild(chip);

    if (indice < resultado.derivacao.length - 1) {
      const seta = document.createElement("span");
      seta.className = "derivation-arrow";
      seta.textContent = ">";
      derivationRibbon.appendChild(seta);
    }
  });
}

function renderizarPassos(resultado) {
  const tabela = document.querySelector("#steps-table");
  tabela.innerHTML = "";

  const thead = document.createElement("thead");
  const trHead = document.createElement("tr");
  ["Passo", "Pilha", "Entrada", "Acao"].forEach((texto) => {
    trHead.appendChild(criarCelula("th", texto));
  });
  thead.appendChild(trHead);
  tabela.appendChild(thead);

  const tbody = document.createElement("tbody");
  resultado.passos.forEach((passo) => {
    const tr = document.createElement("tr");
    tr.className = passo.erro ? "step-row-error" : "step-row-used";
    tr.appendChild(criarCelula("td", String(passo.numero), "code-cell"));
    tr.appendChild(criarCelula("td", passo.pilha, "code-cell"));
    tr.appendChild(criarCelula("td", passo.entrada, "code-cell"));
    tr.appendChild(criarCelula("td", passo.acao, "step-action"));
    tbody.appendChild(tr);
  });

  if (!resultado.passos.length) {
    const tr = document.createElement("tr");
    const td = criarCelula("td", resultado.erro || "Nenhum passo executado.", "step-action");
    td.colSpan = 4;
    tr.appendChild(td);
    tbody.appendChild(tr);
  }

  tabela.appendChild(tbody);
}

function atualizarInterface(sentenca) {
  const resultado = analisar(sentenca);

  resultTitle.textContent = resultado.aceita ? "Sentenca aceita" : "Sentenca rejeitada";
  resultBadge.textContent = resultado.aceita ? "Aceita" : "Rejeitada";
  resultBadge.className = `result-badge ${resultado.aceita ? "accepted" : "rejected"}`;

  renderizarResumo(resultado);
  renderizarDerivacao(resultado);
  renderizarPassos(resultado);
  renderizarParser(resultado.celulasUsadas);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  atualizarInterface(input.value);
});

exampleButton.addEventListener("click", () => {
  input.value = "cbca";
  atualizarInterface(input.value);
  input.focus();
});

renderizarProducoes();
renderizarTabelaSimples("#first-follow-table", firstFollowResolvido);
renderizarTabelaSimples("#stack-table", pilhaResolvida, { cabecalhoVazio: "" });
atualizarInterface(input.value);
