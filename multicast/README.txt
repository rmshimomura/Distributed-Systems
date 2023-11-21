É necessário que exista um arquivo chamado ips.txt na mesma pasta do arquivo multicast_message.py, com os ips dos computadores que receberão a mensagem, um ip por linha.
    - Todos os ips seguem o formato <ip> <nome>
    - É importante também que o ip do computador que está rodando o script esteja no arquivo ips.txt, para que o bind seja feito corretamente, exemplo:
        192.168.15.29 Notebook
        192.168.15.55 Desktop
    - Caso contrário, o código avisará que não existe o ip da máquina no arquivo ips.txt e encerrará a execução.
    - Caso existam 2 ips para a máquina que está rodando o script, o código avisará que existem 2 ips para a máquina e encerrará a execução.

Portas padronizadas:
3000 = Heartbeat
3001 = Mensagens multicast (inseridas manualmente pelo usuário)
3002 = ACK das mensagens multicast

Threads rodando:
    - Uma thread para receber heartbeats
    - Uma thread para enviar heartbeats
    - Uma thread para receber mensagens multicast
    - Uma thread para checar hosts inativos

Intervalo de heartbeats: 2 segundos
Latência: 0 segundos (ajustável no código)
Máximo de retransmissões: 5 (ajustável no código)
Timeout ack mensagens = 1 segundo (delta m)
Timeout padrão: intervalo_heartbeat + timeout_mensagens (delta t)
Timeout para hosts inativos: 2 * delta t

Features disponíveis:

    Checagem de falhas por meio do heartbeats
    Reconexão caso um dos elementos da rede caia e retorne após um tempo
    Envio e recebimento de mensagens multicast através do protocolo UDP com retransmissão
    Envio de ACKs para mensagens multicast recebidas
    Checagem de hosts inativos
    Latência ajustável
    Máximo de retransmissões ajustável
    Exibe os hosts ativos e inativos

Funcionamento do Delta t:

    Delta t = invervalo heartbeat + time_out da mensagem (chamaremos isso de delta_m)
    Delta t padrao = invervalo heartbeat + time_out da mensagem
    
    A partir do envio das mensagens, o delta t é ajustado:
        if tempo_recebimento_ack < delta_t * 2:
            if tempo_recebimento_ack >= delta_t
                delta_m = (tempo_recebimento_ack) - intervalo_heartbeat
                delta_t = delta_m + intervalo_heartbeat
            else:
                delta_m = delta_m / 2
                delta_t = delta_m + intervalo_heartbeat
        else:
            Fail
        
    Caso um host caia, resetamos para o delta t padrão:
        delta_t = delta_t_padrao
    Delta_m = 1


Para executar o arquivo, basta colocar o seguinte comando no terminal:
    python3 multicast_message.py


Para soluções em escala, seria interessante a divisão da rede em subgrupos, onde cada subgrupo teria um servidor responsável por receber as mensagens multicast e retransmiti-las para os outros hosts do subgrupo. Dessa forma, o número de mensagens multicast enviadas seria menor, diminuindo o tráfego na rede. 
Para isso, a eleição de coordenadores seria indispensável.