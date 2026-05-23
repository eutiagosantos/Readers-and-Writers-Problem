# Explicação: Problema dos Leitores e Escritores

> Código Python que demonstra acesso concorrente a um vetor compartilhado `M` usando threads e semáforos.

---

## Cabeçalho e importações

```python
"""Problema dos Leitores e Escritores — vetor M partilhado com threads e semáforos."""
```
**Docstring** do módulo: descreve o propósito geral do arquivo.

```python
import threading
```
Importa o módulo `threading`, que fornece `Thread`, `Semaphore` e `Lock` — as primitivas de concorrência usadas no programa.

```python
import time
```
Importa `time` para usar `time.sleep()` (simular trabalho) e `time.time()` (timestamps nos logs).

---

## Variáveis globais

```python
M = [3, 7, 1, 9]
```
O **recurso compartilhado**: uma lista de 4 inteiros que todos os threads vão ler ou modificar. É o "objeto disputado" do problema.

```python
read_count = 0
```
Contador de quantos leitores estão ativos *no momento*. Controla quando o lock de escrita deve ser adquirido ou liberado.

```python
mutex = threading.Semaphore(1)
```
**Semáforo binário** (valor inicial 1 = livre). Protege o acesso ao `read_count`. Garante que apenas um leitor por vez atualize esse contador — sem isso, dois leitores poderiam incrementar/decrementar `read_count` simultaneamente e corromper o valor.

```python
rw = threading.Semaphore(1)
```
**Semáforo de leitura-escrita** (valor inicial 1 = livre). Controla o acesso exclusivo ao vetor `M`. Um escritor precisa adquirir este semáforo sozinho; leitores só o adquirem quando o *primeiro* leitor entra e o liberam quando o *último* sai.

```python
_log_lock = threading.Lock()
```
**Lock dedicado ao log**. Evita que as mensagens de diferentes threads se misturem no `print`. Um `Lock` é equivalente a `Semaphore(1)`, mas com interface mais idiomática para Python.

---

## Função `_log`

```python
def _log(msg: str) -> None:
```
Define a função de log. Recebe uma string `msg` e não retorna nada (`None`).

```python
    with _log_lock:
```
Adquire `_log_lock` de forma segura usando gerenciador de contexto. Garante que só um thread imprime por vez — o lock é liberado automaticamente ao sair do bloco `with`, mesmo em caso de exceção.

```python
        print(f"[{time.time():.3f}] {msg}", flush=True)
```
Imprime o timestamp atual (3 casas decimais, em segundos desde epoch) seguido da mensagem. `flush=True` força a gravação imediata no terminal, importante em programas concorrentes onde o buffer pode reter saídas fora de ordem.

---

## Função `reader`

```python
def reader(reader_id: str, op: str) -> None:
```
Define o comportamento de um leitor. Recebe um identificador (`reader_id`) e a operação a executar (`op`).

```python
    global read_count
```
Declara que `read_count` refere-se à variável global (não a uma local). Necessário porque a função vai modificar seu valor.

```python
    mutex.acquire()
```
Adquire o semáforo `mutex` **antes** de mexer em `read_count`. Garante exclusão mútua entre leitores que tentam entrar ao mesmo tempo.

```python
    read_count += 1
```
Incrementa o contador de leitores ativos. Operação segura aqui pois está dentro do `mutex`.

```python
    if read_count == 1:
        rw.acquire()
```
**Lógica do primeiro leitor**: se este é o único leitor ativo (contagem passou de 0 para 1), adquire o semáforo `rw`. Isso bloqueia escritores enquanto houver pelo menos um leitor. Leitores subsequentes não precisam adquirir `rw` — eles "carona" no lock já obtido.

```python
    mutex.release()
```
Libera o `mutex` após atualizar `read_count` e, se necessário, adquirir `rw`. O `mutex` nunca fica preso durante a leitura em si — outros leitores podem entrar livremente.

```python
    _log(f"{reader_id} → entrou (leitura)")
```
Registra no log que o leitor entrou na seção crítica de leitura.

```python
    time.sleep(0.08)
```
Simula 80ms de processamento (tempo de leitura). Durante este sleep o semáforo `rw` permanece adquirido pelo grupo de leitores, bloqueando escritores.

```python
    if op == "index_3":
        value = M[3]
        _log(f"{reader_id}: M[3] = {value}")
```
Operação `index_3`: lê apenas o índice 3 do vetor e loga o valor encontrado.

```python
    elif op == "full":
        snapshot = list(M)
        _log(f"{reader_id}: M = {snapshot}")
```
Operação `full`: cria uma cópia completa de `M` (`list(M)`) e loga o estado inteiro. Usar `list()` garante que o snapshot é imutável em relação a escritas futuras.

```python
    elif op == "index_1":
        value = M[1]
        _log(f"{reader_id}: M[1] = {value}")
```
Operação `index_1`: lê apenas o índice 1 do vetor e loga o valor.

```python
    _log(f"{reader_id} ← saiu (leitura)")
```
Registra no log que o leitor concluiu e está saindo da seção crítica.

```python
    mutex.acquire()
```
Adquire `mutex` novamente para modificar `read_count` com segurança.

```python
    read_count -= 1
```
Decrementa o contador: este leitor não está mais ativo.

```python
    if read_count == 0:
        rw.release()
```
**Lógica do último leitor**: se não há mais leitores ativos, libera o semáforo `rw`. Isso permite que escritores bloqueados possam adquirir `rw` e entrar na seção crítica.

```python
    mutex.release()
```
Libera o `mutex`. A saída do leitor está completa.

---

## Função `writer`

```python
def writer(writer_id: str, op: str) -> None:
```
Define o comportamento de um escritor. Recebe identificador e operação.

```python
    rw.acquire()
```
Adquire o semáforo `rw` **diretamente** — sem `mutex`. O escritor precisa de acesso exclusivo total: nenhum outro escritor ou leitor pode estar ativo. Se `rw` já estiver em posse de leitores ou de outro escritor, este thread fica bloqueado aqui até ser liberado.

```python
    _log(f"{writer_id} → entrou (escrita)")
```
Registra no log que o escritor entrou na seção crítica.

```python
    time.sleep(0.08)
```
Simula 80ms de processamento. O lock `rw` permanece adquirido durante todo esse tempo.

```python
    if op == "set_index_3":
        M[3] = 2
        _log(f"{writer_id}: M[3] = 2  →  M = {list(M)}")
```
Operação `set_index_3`: altera apenas o índice 3 para o valor `2` e loga o estado completo resultante.

```python
    elif op == "set_all":
        new_values = [2, 1, 0, 6]
        for i, v in enumerate(new_values):
            M[i] = v
        _log(f"{writer_id}: M = {new_values}")
```
Operação `set_all`: define os novos valores para todos os 4 índices usando `enumerate()` (que retorna pares `(índice, valor)`). Como `rw` está adquirido, nenhum leitor verá `M` em estado parcialmente atualizado durante o loop.

```python
    _log(f"{writer_id} ← saiu (escrita)")
```
Registra no log que o escritor concluiu e está saindo.

```python
    rw.release()
```
Libera `rw`. O próximo thread bloqueado (leitor ou escritor) pode agora adquirir o semáforo.

---

## Função `main`

```python
def main() -> None:
```
Ponto de entrada da lógica principal do programa.

```python
    _log(f"Estado inicial: M = {list(M)}")
```
Loga o estado inicial do vetor antes de qualquer thread ser criada.

```python
    threads = [
        threading.Thread(target=writer, args=("e1", "set_index_3"), name="e1"),
        threading.Thread(target=writer, args=("e2", "set_all"),       name="e2"),
        threading.Thread(target=reader, args=("l1", "index_3"),       name="l1"),
        threading.Thread(target=reader, args=("l2", "full"),          name="l2"),
        threading.Thread(target=reader, args=("l3", "index_1"),       name="l3"),
    ]
```
Cria uma lista com 5 threads:
- **e1** — escritor que altera só `M[3]`
- **e2** — escritor que reescreve todo `M`
- **l1** — leitor que lê `M[3]`
- **l2** — leitor que lê `M` inteiro
- **l3** — leitor que lê `M[1]`

`target` define a função a executar; `args` os argumentos; `name` é um rótulo para depuração.

```python
    for t in threads:
        t.start()
```
Inicia todos os threads. A partir daqui, escritores e leitores competem pelo acesso a `M` conforme as regras dos semáforos. A ordem real de execução depende do escalonador do sistema operacional.

```python
    for t in threads:
        t.join()
```
Bloqueia o thread principal até que **todos** os threads terminem. Sem `join()`, o programa principal poderia encerrar antes dos threads filhos completarem.

```python
    _log(f"Estado final: M = {list(M)}")
```
Loga o estado final de `M` após todas as operações terem concluído.

---

## Bloco de execução

```python
if __name__ == "__main__":
    main()
```
Padrão Python: executa `main()` somente quando o arquivo é rodado diretamente (não quando importado como módulo). Isso permite que o código seja reutilizável como biblioteca sem disparar threads automaticamente.

---

## Resumo do fluxo de semáforos

| Situação | `mutex` | `rw` |
|---|---|---|
| Primeiro leitor entra | Adquire → libera | Adquire |
| Leitores intermediários entram | Adquire → libera | — |
| Último leitor sai | Adquire → libera | Libera |
| Escritor entra | — | Adquire |
| Escritor sai | — | Libera |

> **Nota sobre starvation**: esta implementação favorece leitores. Se leitores chegarem continuamente, escritores podem esperar indefinidamente pois `rw` nunca chega a ser liberado. Soluções mais robustas usam filas de espera ou semáforos adicionais para garantir equidade.
