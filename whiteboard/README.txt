Os testes serão realizados no localhost como definido no dia 20/11/2023 às 15:25 com o professor via Google meet.
Antes de inicar, é importante que as portas estejam definidas no arquivo ports.txt,
seguindo o formato <nome_da_instancia> <porta>.


Exemplo:

node_1 1000
node_2 2000
node_3 3000
node_4 4000

Para rodar os códigos, por favor siga o padrão:

    python ./connection <nome_da_instancia>

A interpretação usada nesse trabalho, é que cada instância só pode ter uma função, ou um servidor ou um cliente.
Para isso, é necessário que o usuário escolha qual função a instância terá.
O problema de fazer função dupla nesse trabalho é organizar os sockets que irão estar escutando em cada porta.

Existem algumas funções que podem ser chamadas no terminal para testar o funcionamento do sistema:

    1. Criar quadro (a instância vira um servidor).
    2. Descobrir quadros disponíveis entre as instâncias.
    3. Conectar-se a um quadro (é possível que uma instância do tipo servidor se conecte APENAS ao quadro que ela criou. Caso contrário, a instância vira um cliente do quadro solicitado).
    4. Limpar o terminal.
    5. Sair do programa.

A forma geométrica disponibilizada é uma linha, onde o usuário define dois pontos a partir do clique ESQUERDO do mouse.
Para mover uma linha, clique com o botão DIREITO do mouse para arrastá-la.
    - Durante essa movimentação, a exclusão mútua entra em ação, impedindo que outros usuários movam a linha, mostrando uma mensagem no terminal.

As operações de exclusão mútua e eleição foram implementadas.

Quando um servidor com um quadro criado e clientes desse quadro estão conectados cai, o processo de eleição inicia-se automaticamente.
    - O nó que detectou primeiro a falha é eleito o novo servidor.
    - Neste momento, todas as janelas que estavam conectadas ao quadro caído são desconectadas.
        - Para conectar novamente, é necessário que os clientes se conectem ao novo servidor.