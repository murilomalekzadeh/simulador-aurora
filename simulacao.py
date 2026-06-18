
def simulacao_completa(prob_cliente_normal_recrutar = 0.03,
                        prob_retencao = 0.80,
                        prob_bom_recrutador = 0.2,
                        prob_bom_recrutador_filho = 0.3,
                        prob_venda_prime = 0.08,
                        meses_simulacao = 60,
                        valor_final = 60,
                        pct_comissao_prime = 0.215,
                        ponto_prime_a_cada_x_reais = 6.37,
                        ponto_recompra_a_cada_x_reais = 5,
                        pontos_de_recrutamento = 400,
                        comissao_recrutamento_pai = 350,
                        comissao_recrutamento_avo = 50,
                        #forma_de_evolucao = 'linear'
                        forma_de_evolucao = 'exponencial',
                        #tipo_analise = 'historico'
                        tipo_analise = 'último mes',
                        callback_status=None):

    import pandas as pd
    import numpy as np
    from collections import defaultdict
    import time
    import os
    import random

    if callback_status:
        callback_status("Realizando leitura dos parâmetros escolhidos...")
        time.sleep(1)


    # Criterios para classificacao.
    # Inserir VG, V3, PML
    # se não houver restrição de PML utilizar float("inf")
    categorias = [
        ("Afiliado", 0, 0, float("inf")),
        ("Influencer 1k", 1000, 1000, float("inf")),
        ("Influencer 5k", 5000, 2000, float("inf")),
        ("Team Builder 10k", 10000, 4000, 5000),
        ("Team Builder 20k", 20000, 6000, 10000),
        ("Team Builder 30k", 30000, 8000, 15000),
        ("Team Leader 50k", 50000, 10000, 20000),
        ("Team Leader 100k", 100000, 15000, 40000),
        ("Team Leader 150k", 150000, 20000, 60000),
        ("Legacy Maker 200k", 200000, 30000, 80000),
        ("Legacy Maker 400k", 400000, 30000, 160000),
        ("Legacy Maker 600k", 600000, 30000, 240000),
        ("Legend 1M", 1000000, 30000, 400000),
        ("Legend 3M", 3000000, 30000, 1200000),
        ("Legend 5M", 5000000, 30000, 2000000),
    ]

    ordem_categorias = [categoria[0] for categoria in categorias]

    # Bonus Produção
    # Porcentagem de Bonus que cada nível ganha de seu VG
    pct_bonus = {
        "Influencer 1k": 0.04,
        "Influencer 5k": 0.08,
        "Team Builder 10k": 0.12,
        "Team Builder 20k": 0.12,
        "Team Builder 30k": 0.12,
        "Team Leader 50k": 0.12,
        "Team Leader 100k": 0.12,
        "Team Leader 150k": 0.12,
        "Legacy Maker 200k": 0.12,
        "Legacy Maker 400k": 0.12,
        "Legacy Maker 600k": 0.12,
        "Legend 1M": 0.12,
        "Legend 3M": 0.12,
        "Legend 5M": 0.12
    }

    # Bonus Construtor recebido em cada nível
    bonus_construtor_map = {
        "Team Builder 10k": 1000.0,
        "Team Builder 20k": 2000.0,
        "Team Builder 30k": 3000.0,
        "Team Leader 50k": 3000.0,
        "Team Leader 100k": 3000.0,
        "Team Leader 150k": 3000.0,
        "Legacy Maker 200k": 3000.0,
        "Legacy Maker 400k": 3000.0,
        "Legacy Maker 600k": 3000.0,
        "Legend 1M": 3000.0,
        "Legend 3M": 3000.0,
        "Legend 5M": 3000.0
    }

    # categorias elegíveis ao bonus_lideranca, estrutura abaixo:
    # "Nome do Nível" : (porcentagem_recebida, geracoes_permitidas)
    bonus_lideranca_map = {
        "Team Builder 10k":  (0.05, 3),
        "Team Builder 20k":  (0.05, 4),
        "Team Builder 30k":  (0.05, 5),
        "Team Leader 50k":   (0.05, 6),
        "Team Leader 100k":  (0.05, 7),
        "Team Leader 150k":  (0.05, 8),
        "Legacy Maker 200k": (0.05, 8),
        "Legacy Maker 400k": (0.05, 8),
        "Legacy Maker 600k": (0.05, 8),
        "Legend 1M":         (0.05, 8),
        "Legend 3M":         (0.05, 8),
        "Legend 5M":         (0.05, 8),
    }

    # Quantidade de cotas para cada nível
    cotas_map = {
        "Team Leader 50k":   5,
        "Team Leader 100k":  10,
        "Team Leader 150k":  15,
        "Legacy Maker 200k": 20,
        "Legacy Maker 400k": 40,
        "Legacy Maker 600k": 60,
        "Legend 1M":         100,
        "Legend 3M":         100,
        "Legend 5M":         100,
    }

    porcentagem_vtp_distribuido_global_pool = 0.05


    def gerar_filhos(n=1, p=prob_cliente_normal_recrutar):
        return np.random.binomial(n, p)  # média ~1.2

    def gerar_filhos_hist(qtdFilhos_ant, estrela, filtro):
        if estrela == 1 and filtro == 0:
            return min(max(2, np.random.binomial(qtdFilhos_ant*2, 0.5)), 10)
        elif filtro == 1:
            return gerar_filhos(n=1, p=0.03)
        elif qtdFilhos_ant == 0:
            return gerar_filhos()
        else:
            return min(np.random.binomial(qtdFilhos_ant*2, 0.5), 4)
        
    # RECEITA (Gamma Inversa)
    def gerar_receita(alpha=5, beta=10000):
        gamma_sample = np.random.gamma(shape=alpha, scale=1/beta)
        return min(100000, max(round(1 / gamma_sample, 2) / 4, 1000))


    def gerar_receita_hist(receita_ant):
        alpha = 8
        beta = max(receita_ant * (alpha - 1), 1)
        gamma_sample = np.random.gamma(
            shape=alpha,
            scale=1/beta)
        return min(100000, max(round(1 / gamma_sample, 2), 1000))

    def gerar_retencao(qtdFilhos_ant):

        if qtdFilhos_ant > 0:
            prob = 1
        else:
            prob = 1 #prob_retencao

        # sorteio Bernoulli
        return np.random.binomial(1, prob)

    # Preciso deixar criada a variavel global aqui
    idPessoa_global = 1
    def nascimento(mes, direto, idPatrocinador = np.nan, pai_estrela = 0):

        # Criando um novo idPessoa
        nonlocal idPessoa_global
        idPessoa = idPessoa_global
        idPessoa_global += 1
        
        # Inserindo volume de filhos
        if direto == 0:
            qtdFilhos = 0
        else:
            qtdFilhos = gerar_filhos()

        # Sempre a receita é o valor de entrada e o estagio é zero
        Receita = 2790
        estagio = 0

        # Clientes premium
        # 1. Check se vendeu algum
        flg_cliente_premium = np.random.binomial(1, prob_venda_prime)
        
        # 2) quantidade vendida
        if flg_cliente_premium == 1:
            
            # lambda baixo => maioria em 1 item
            qtd = np.random.poisson(lam=1.2)
            
            # Venda entre 1 e 20 produtos de 127
            Receita_cliente = 127 * min(max(qtd, 1), 20)
        
        else:
            Receita_cliente = 0

        
        # Verificando se a pessoa vai dar churn no próximo mês
        flg_retencao = gerar_retencao(qtdFilhos)

        if pai_estrela == 1:
            estrela = np.random.binomial(1, prob_bom_recrutador_filho) # X% são estrelas
        else:
            estrela = np.random.binomial(1, prob_bom_recrutador) # Y% são estrelas
        
        # retorna dict
        return {'Mes': mes, 'idPessoa': idPessoa, 'estagio': estagio, 'direto': direto, 'qtdFilhos': qtdFilhos, 'Receita': Receita, 'Receita_cliente': Receita_cliente, 
                    'flg_retencao': flg_retencao, 'idPatrocinador': idPatrocinador, 'estrela': estrela}

    def envelhecimento(mes, idPessoa, estagio, direto, qtdFilhos_ant, Receita_ant, Receita_cliente_ant, idPatrocinador, estrela, filtro):

        # Novo mês
        mes += 1
        
        # Aumentando estagio até no máximo 2
        estagio = min(estagio + 1, 2)
        
        # Inserindo volume de filhos
        if direto + estagio == 1: # ou é direto=1 e esta no estagio 0, ou nao é direto e esta no estagio 1
            qtdFilhos = gerar_filhos()
        else:
            qtdFilhos = gerar_filhos_hist(qtdFilhos_ant, estrela, filtro)

        # Inserindo Receita no mês
        if estagio == 1:
            Receita = gerar_receita()
        else:
            Receita = gerar_receita_hist(Receita_ant)
        
        # Clientes premium
        # Se não vendeu nada mes passado volta pro sorteio normal
        if Receita_cliente_ant == 0:
            # 1. Check se vendeu algum (8% de chance de vender)
            flg_cliente_premium = np.random.binomial(1, prob_venda_prime)
            
            # 2) quantidade vendida
            if flg_cliente_premium == 1:
                
                # lambda baixo => maioria em 1 item
                qtd = np.random.poisson(lam=1.2)
                
                # Venda entre 1 e 20 produtos de 127
                Receita_cliente = 127 * min(max(qtd, 1), 20)
            else:
                Receita_cliente = 0
        
        else:
            # Probabilidade de ter venda premium considerando vendas no mês passado
            score = -1.0 + 0.06 * np.sqrt(Receita_cliente_ant)
            p_venda = 1 / (1 + np.exp(-score))
            flg_cliente_premium = np.random.binomial(1, p_venda)
        
            # quantidade
            if flg_cliente_premium == 1:
                # transforma receita anterior em "quantidade histórica"
                qtd_base = Receita_cliente_ant / 127
                lam = 3 * np.sqrt(qtd_base)
                qtd = np.random.poisson(lam)
                # garante mínimo 1
                Receita_cliente = 127 * max(qtd, 1)
            else:
                Receita_cliente = 0

        # Verificando se a pessoa vai dar churn no próximo mês
        flg_retencao = gerar_retencao(qtdFilhos_ant)
        
        # retorna dict
        return {'Mes': mes, 'idPessoa': idPessoa, 'estagio': estagio, 'direto': direto, 'qtdFilhos': qtdFilhos, 'Receita': Receita, 'Receita_cliente': Receita_cliente, 
                'flg_retencao': flg_retencao, 'idPatrocinador': idPatrocinador, 'estrela': estrela}

    # Meses de simulacao
    if forma_de_evolucao == 'logaritmica': 
        meses = {i: round(1 + (valor_final - 1) * np.log(i + 1) / np.log(meses_simulacao + 1)) for i in range(meses_simulacao + 1)}
    else: 
        meses = {i: round(1 + (valor_final - 1)* i/ meses_simulacao)for i in range(meses_simulacao + 1)}

    meses = {k: v * 1000 for k, v in meses.items()}

    # Criando rede
    SEED = 42
    random.seed(SEED)
    np.random.seed(SEED)
    os.environ["PYTHONHASHSEED"] = str(SEED)


    inicio = time.time()

    # Criando variáveis globais
    tabela_lista = []
    #idPessoa_global = 1 # Antes era global e ficava aqui

    for mes_iter, max_linhas in meses.items():


        if callback_status:
            callback_status("Criando rede (Mês =" + str(mes_iter) +  ")")
        
        qtd_linhas = 0
        argumentos_pai = [mes_iter, 1]

        # Contando pessoas ativas no mes anterior
        if mes_iter > 0:
            qtd_ativas_mes = sum(1 for x in tabela_lista if x['Mes'] == (mes_iter) and x['flg_retencao'] == 1)
        else:
            qtd_ativas_mes = 0
        
        for _ in range(max_linhas):

            if qtd_linhas + qtd_ativas_mes >= max_linhas:
                qtd_linhas  = 0
                break

            # Faço um sorteio 1 já salvo na tabela
            registro = nascimento(*argumentos_pai)
            tabela_lista.append(registro)
            qtd_linhas += 1
            # separo algumas para o sortear os filhos
            qtd_filhos_raiz = registro['qtdFilhos']
            idPatrocinador = registro['idPessoa']
            pai_estrela = registro['estrela']
            
            for i in range(qtd_filhos_raiz):
                registro = nascimento(mes_iter, 0, idPatrocinador = idPatrocinador, pai_estrela = pai_estrela)
                tabela_lista.append(registro)
                qtd_linhas += 1

        ## novo
        filtrado = [x for x in tabela_lista if x['Mes'] == mes_iter]
        
        for pessoa in filtrado:
            if qtd_linhas + qtd_ativas_mes >= max_linhas:
                filtro  = 1
            else:
                filtro = 0

            if pessoa['flg_retencao'] == 0:
                continue
            else:
                registro = envelhecimento(
                mes=pessoa['Mes'],
                idPessoa = pessoa['idPessoa'],
                estagio=pessoa['estagio'],
                direto=pessoa['direto'],
                qtdFilhos_ant=pessoa['qtdFilhos'],
                Receita_ant=pessoa['Receita'],
                Receita_cliente_ant=pessoa['Receita_cliente'],
                idPatrocinador=pessoa['idPatrocinador'],
                estrela=pessoa['estrela'],
                filtro = filtro
            )
            tabela_lista.append(registro)
        
            # separo algumas para o sortear os filhos
            qtd_filhos_raiz = registro['qtdFilhos']
            idPatrocinador = registro['idPessoa']
            mes = registro['Mes']
        
            for i in range(qtd_filhos_raiz):
                    registro = nascimento(mes, 0, idPatrocinador = idPatrocinador)
                    tabela_lista.append(registro)
                    qtd_linhas += 1

        fim = time.time()
        print(f"mes {mes_iter}, Tempo: {fim - inicio:.4f} segundos")

    df = pd.DataFrame(tabela_lista)

    # A lógica é rodar tudo por mês, mas uma pessoa pode se tornar inativa e sair da tabela
    # Isso vai quebrar a sequencia de pai-filho, entao vou fazer uma tabela e um dict auxiliar para manter todas as relacoes
    tb_patrocinador = (df[['idPessoa', 'idPatrocinador']].drop_duplicates().reset_index(drop=True))

    if tipo_analise == 'último mes':
        df = df[df['Mes'] == meses_simulacao]

    if callback_status:
        callback_status("Calculando pontuações e categorias de cada consultor...")
        time.sleep(2)
        callback_status("Calculando Bônus Recrutamento... (1/7)")
        time.sleep(2)
        callback_status("Calculando Bônus Cliente Prime... (2/7)")


    # Pontuações simples:
    # 1. Bonus Cliente Prime: Se um cliente prime que eu cadastrei gasta 6,37 reais, eu ganho 1 ponto
    # A cada 5 reais que eu gasto comprando, eu ganho 1 ponto (exceto na compra inicial, estagio=0)
    # A pessoa que entra compra o kit e ganha 400 pontos

    df['comissao_cliente_prime'] = df['Receita_cliente'] * pct_comissao_prime
    df['pontos_cliente_prime'] = (df['Receita_cliente'] / ponto_prime_a_cada_x_reais).astype(int)
    df['pontos_compra'] = (df['Receita'] / ponto_recompra_a_cada_x_reais).where(df['estagio'] != 0, 0)
    df.loc[df['estagio'] == 0, 'bonus_compra'] = 0
    df['pontos_recrutamento'] = np.where(df['estagio'] == 0, pontos_de_recrutamento, 0)

    # Bonus 2: De entrada (Recrutamento)
    #
    # Regra:
    # Se eu recrutei: ganho 350 de comissão e 400 pontos
    # Se um recrutado meu recruta (um neto): eu ganho 50 reais de comissao
    df['comissao_recrutamento'] = 0

    # Crio uma tabela por fora com novos nomes das colunas (com todos filhos, não só do mês)
    edges = (tb_patrocinador[['idPatrocinador', 'idPessoa']].dropna()
        .rename(columns={'idPatrocinador': 'pai','idPessoa': 'filho'}))

    for mes, df_mes in df.groupby('Mes'):

        # ----------------------------
        # nível 0 (quem conta pontos)
        # ----------------------------
        df0 = df_mes[df_mes['estagio'] == 0]

        nivel1 = df0.groupby('idPatrocinador').size()

        comissao1 = nivel1 * comissao_recrutamento_pai


        # ----------------------------
        # nível 2 (netos com estagio 0, as quais vamos saber quem ganha a comissão dela)
        # ----------------------------
        validos = set(df0['idPessoa'])

        g2 = (
            edges.merge(edges, left_on='filho', right_on='pai', how='inner')
                .rename(columns={'pai_x': 'pai', 'filho_y': 'neto'})
        )

        g2 = g2[g2['neto'].isin(validos)]

        nivel2 = g2.groupby('pai').size()
        comissao2 = nivel2 * comissao_recrutamento_avo

        # ----------------------------
        # junta tudo
        # ----------------------------
        resultado = (
            comissao1.add(comissao2, fill_value=0)
            .to_frame('comissao')
            .fillna(0)
        )

        mask = df['Mes'] == mes

        df.loc[mask, 'comissao_recrutamento'] = df.loc[mask, 'idPessoa'].map(resultado['comissao']).fillna(0)

    # Agora tenha a minha pontuação individual (VTP), a soma das 3:
    # Meus recrutamentos, compras dos meus clientes prime, e minhas compras.
    df["VTP"] = (df["pontos_recrutamento"] + df["pontos_cliente_prime"] + df["pontos_compra"])

    #Estou lidando com o problema de eu fazer os cálculos por mês e correr risco de perder a conexão por inativação
    filhos_global = defaultdict(list)

    for pessoa, patrocinador in zip(
        tb_patrocinador["idPessoa"],
        tb_patrocinador["idPatrocinador"]
    ):
        if pd.notna(patrocinador):
            filhos_global[patrocinador].append(pessoa)


    # Aqui eu calculo o valor da minha rede
    # V3: pontuação de meus filhos, netos e bisnetos
    # VG: pontuação de todos abaixo de mim (eu não conta)
    # PML para calcular VG e V3, para verificar a regra do PML (complicada nao vou explicar aqui)
    def calcula_metricas_mes(df_mes):

        df_mes = df_mes.copy()

        # lookup dos pontos individuais
        vtp = dict(zip(df_mes["idPessoa"], df_mes["VTP"]))

        # patrocinador -> filhos
        filhos = filhos_global

        # ---------------------------------------------------
        # cache para evitar recalcular subárvores
        # ---------------------------------------------------
        total_rede_cache = {}

        def total_rede(pessoa):
            """
            volume da pessoa + toda sua descendência
            """
            if pessoa in total_rede_cache:
                return total_rede_cache[pessoa]

            total = vtp.get(pessoa, 0)

            for filho in filhos.get(pessoa, []):
                total += total_rede(filho)

            total_rede_cache[pessoa] = total
            return total

        # ---------------------------------------------------
        # VG
        # ---------------------------------------------------
        vg = {}

        for pessoa in df_mes["idPessoa"]:

            soma = 0

            for filho in filhos.get(pessoa, []):
                soma += total_rede(filho)

            vg[pessoa] = soma

        # ---------------------------------------------------
        # V3
        # ---------------------------------------------------
        v3 = {}

        for pessoa in df_mes["idPessoa"]:

            soma = 0

            for filho in filhos.get(pessoa, []):

                soma += vtp.get(filho, 0)

                for neto in filhos.get(filho, []):
                    soma += vtp.get(neto, 0)

                    for bisneto in filhos.get(neto, []):
                        soma += vtp.get(bisneto, 0)

            v3[pessoa] = soma

        # ---------------------------------------------------
        # PML_test_vg
        # ---------------------------------------------------
        pml_vg = {}

        for pessoa in df_mes["idPessoa"]:

            pml_vg[pessoa] = [
                total_rede(filho)
                for filho in filhos.get(pessoa, [])
            ]

        # ---------------------------------------------------
        # PML_test_v3
        # ---------------------------------------------------
        pml_v3 = {}

        for pessoa in df_mes["idPessoa"]:

            lista = []

            for filho in filhos.get(pessoa, []):

                volume = vtp.get(filho, 0)

                for neto in filhos.get(filho, []):
                    volume += vtp.get(neto, 0)

                    for bisneto in filhos.get(neto, []):
                        volume += vtp.get(bisneto, 0)

                lista.append(volume)

            pml_v3[pessoa] = lista

        # grava colunas
        df_mes["VG"] = df_mes["idPessoa"].map(vg)
        df_mes["V3"] = df_mes["idPessoa"].map(v3)
        df_mes["PML_test_vg"] = df_mes["idPessoa"].map(pml_vg)
        df_mes["PML_test_v3"] = df_mes["idPessoa"].map(pml_v3)

        return df_mes


    # Aqui é pra eu rodar todos os meses
    def calcula_metricas(df):

        resultado = []

        for _, df_mes in df.groupby("Mes"):
            resultado.append(
                calcula_metricas_mes(df_mes)
            )

        return pd.concat(resultado, ignore_index=True)
    df = calcula_metricas(df)

    # Marcação de categoria
    # Com V3, VG e PML vejo em qual categoria cada revendedor está



    def calcula_categoria(vtp, pml_vg, pml_v3):
    # Note que essa forma testa todas as categorias e pega a mais alta
    # Se a pessoa não passar em uma categoria baixo e passar na de cima, então é a de cima
        def soma_com_teto(lista, teto):
            return sum(min(x, teto) for x in lista)

        categoria_final = "Afiliado"

        for nome, vg_min, v3_min, pml_max in categorias:

            vg = soma_com_teto(pml_vg, pml_max) + vtp
            v3 = soma_com_teto(pml_v3, pml_max)

            if vg >= vg_min and v3 >= v3_min:
                categoria_final = nome

        return categoria_final


    df["Categoria"] = df.apply(
        lambda r: calcula_categoria(
            r["VTP"],
            r["PML_test_vg"],
            r["PML_test_v3"]
        ),
        axis=1
    )

    # 3. Bonus de equipe (pt1)
    # Na cédula seguinte coloca de fato na tabela
    # Essa regra é simples: eu posso ganhar 5%-15% da pontuação dos meus filhos, netos e bisnetos dependendo da minha categoria

    if callback_status:
        callback_status("Calculando Bônus Equipe... (3/7)")
    time.sleep(1)
    categorias_team_builder_20k_ou_superior = {"Team Builder 20k", "Team Builder 30k", "Team Leader 50k", "Team Leader 100k", "Team Leader 150k", 
                                            "Legacy Maker 200k", "Legacy Maker 400k", "Legacy Maker 600k", "Legend 1M", "Legend 3M", "Legend 5M"}

    def get_nivel(pessoa, filhos, nivel_max=3):
        niveis = {1: [], 2: [], 3: []}

        idpessoa_atual = [pessoa]
        visitados = set()

        for nivel in range(1, nivel_max + 1):
            prox_idpessoa = []

            for p in idpessoa_atual:
                for f in filhos.get(p, []):
                    if f not in visitados:
                        niveis[nivel].append(f)
                        prox_idpessoa.append(f)
                        visitados.add(f)

            idpessoa_atual = prox_idpessoa

        return niveis

    def calcula_bonus(pessoa, filhos, vtp, categoria):

        niveis = get_nivel(pessoa, filhos, nivel_max=3)

        filhos_ = niveis[1]
        netos_ = niveis[2]
        bisnetos_ = niveis[3]

        bonus = np.float64(0)

        # Afiliado
        if categoria == "Afiliado":
            bonus += 0.05 * sum(vtp.get(f, 0) for f in filhos_)

        # Influencer
        elif categoria in ["Influencer 1k", "Influencer 5k"]:
            bonus += 0.10 * sum(vtp.get(f, 0) for f in filhos_)

        # Team Builder 10k
        elif categoria == "Team Builder 10k":
            bonus += 0.15 * sum(vtp.get(f, 0) for f in filhos_)
            bonus += 0.05 * sum(vtp.get(f, 0) for f in netos_)
        
        # Team Builder 20k
        elif categoria in categorias_team_builder_20k_ou_superior:
            bonus += 0.15 * sum(vtp.get(f, 0) for f in filhos_)
            bonus += 0.05 * sum(vtp.get(f, 0) for f in netos_)
            bonus += 0.05 * sum(vtp.get(f, 0) for f in bisnetos_)

        return bonus


    # 3. Bonus de equipe (pt2)
    # Aqui eu aplico o bonus_equipe direto na base
    df["bonus_equipe"] = 0.0

    for mes, df_mes in df.groupby("Mes"):

        vtp = dict(zip(df_mes["idPessoa"], df_mes["VTP"]))

        bonus = df_mes.apply(
            lambda r: calcula_bonus(r["idPessoa"], filhos_global, vtp, r["Categoria"]),
            axis=1
        )

        df.loc[df_mes.index, "bonus_equipe"] = bonus

    # 4. Bonus de Produção
    # pode ganhar 4-8% do seu VG em função de sua categoria
    # Mas se você vai ganhar 8% de uma perna, mas a pessoa já ganhou X pontos nessa perna, então não posso ganhar de novo
    # É a lógica Breakway
    if callback_status:
        callback_status("Calculando Bônus Produção... (4/7)")
    time.sleep(1)
    pat_map_global = dict(
            zip(tb_patrocinador["idPessoa"],
                tb_patrocinador["idPatrocinador"]))


    def calcular_bonus_producao(df, tb_patrocinador):

        resultados = []

        for mes, df_mes in df.groupby("Mes"):

            df_mes = df_mes.copy()
            id_set = set(df_mes["idPessoa"])

            pct_map = dict(
                zip(
                    df_mes["idPessoa"],
                    df_mes["Categoria"].map(pct_bonus)
                )
            )

            bonus_teorico_map = dict(
                zip(
                    df_mes["idPessoa"],
                    df_mes["Categoria"].map(pct_bonus) * df_mes["VG"]
                )
            )

            bonus_pago_abaixo = defaultdict(float)
            bonus_producao = {}

            ids_ordenados = sorted(id_set, reverse=True)

            def propagar_acima(node, valor):
                pat = pat_map_global.get(node)
                if pat is None:
                    return
                # SOMA: cada filho contribui independentemente
                bonus_pago_abaixo[pat] += valor
                # Se inativo, continua subindo — mas com max para não duplicar
                # o mesmo fluxo passando por pontes diferentes
                if pat not in id_set:
                    propagar_acima(pat, valor)

            for pid in ids_ordenados:

                pct = pct_map.get(pid)

                if pd.isna(pct):
                    propagar_acima(pid, bonus_pago_abaixo[pid])
                    bonus_producao[pid] = 0.0
                    continue

                desconto = bonus_pago_abaixo[pid]
                bonus_real = max(0.0, bonus_teorico_map[pid] - desconto)
                bonus_producao[pid] = bonus_real

                propagar_acima(pid, bonus_real + desconto)

            resultado_mes = pd.DataFrame({
                "Mes": mes,
                "idPessoa": list(id_set)
            })

            resultado_mes["bonus_teorico"] = (
                resultado_mes["idPessoa"]
                .map(bonus_teorico_map)
            )

            resultado_mes["bonus_producao"] = (
                resultado_mes["idPessoa"]
                .map(bonus_producao)
                .fillna(0.0)
            )

            resultados.append(resultado_mes)

        return pd.concat(resultados, ignore_index=True)


    # Uso
    df_bonus = calcular_bonus_producao(df, tb_patrocinador)

    df = df.merge(
        df_bonus,
        on=["Mes", "idPessoa"],
        how="left",
        validate="one_to_one"
    )


    # 5. Bonus construtor
    # Se você é Team Builder vc recebe um tanto fixo (mas se tiver alguém da mesma categoria ou maior, então você não ganha nada)
    if callback_status:
        callback_status("Calculando Bônus Construtor... (5/7)")   
    time.sleep(1)

    hierarquia = {cat[0]: i for i, cat in enumerate(categorias)}

    def calcular_bonus_construtor(df_mes, pat_map_global):

        df_mes = df_mes.copy()

        id_set = set(df_mes["idPessoa"])

        cat_map = dict(zip(df_mes["idPessoa"], df_mes["Categoria"]))

        maior_nivel_abaixo = defaultdict(lambda: -1)
        bonus = {}

        ids = sorted(id_set, reverse=True)

        def propagar_acima(node, nivel):
            pat = pat_map_global.get(node)
            if pat is None:
                return
            maior_nivel_abaixo[pat] = max(maior_nivel_abaixo[pat], nivel)
            # Se inativo, continua subindo
            if pat not in id_set:
                propagar_acima(pat, nivel)

        for pid in ids:

            categoria = cat_map.get(pid)
            nivel_pid = hierarquia.get(categoria, -1)

            # Propaga o maior entre o próprio nível e o que veio de baixo
            nivel_a_propagar = max(nivel_pid, maior_nivel_abaixo[pid])
            propagar_acima(pid, nivel_a_propagar)

            if categoria in bonus_construtor_map:
                if maior_nivel_abaixo[pid] < min(nivel_pid, 5):
                    bonus[pid] = bonus_construtor_map[categoria]
                else:
                    bonus[pid] = 0.0
            else:
                bonus[pid] = 0.0

        df_mes["bonus_construtor"] = df_mes["idPessoa"].map(bonus)

        return df_mes[["idPessoa", "bonus_construtor"]]


    # Loop por mês
    resultados = []

    for mes, df_mes in df.groupby("Mes"):
        resultado_mes = calcular_bonus_construtor(df_mes, pat_map_global)
        resultado_mes["Mes"] = mes
        resultados.append(resultado_mes)

    df_bonus = pd.concat(resultados, ignore_index=True)

    df = df.merge(
        df_bonus,
        on=["Mes", "idPessoa"],
        how="left",
        validate="one_to_one"
    )


    # 6. Bonus Liderança - das gerações

    if callback_status:
        callback_status("Calculando Bônus Liderança, isso pode levar alguns minutos... (6/7)")
    time.sleep(1)


    # índice hierárquico >= 3 = separador de geração
    SEPARADOR_IDX = hierarquia["Team Builder 10k"]


    def calcular_bonus_lideranca(df_mes: pd.DataFrame, pat_map_global: dict) -> pd.DataFrame:
        from collections import defaultdict, deque

        df = df_mes.copy()
        id_set = set(df["idPessoa"])

        # mapas de volume/categoria — apenas ativos
        vtp_map = df.set_index("idPessoa")["VTP"].to_dict()
        vg_map  = df.set_index("idPessoa")["VG"].to_dict()
        cat_map = df.set_index("idPessoa")["Categoria"].to_dict()

        # children_map global — inclui inativos como pontes
        children_map = defaultdict(list)
        for pessoa, pat in pat_map_global.items():
            if pat is not None:
                children_map[pat].append(pessoa)

        def eh_separador(pid):
            return hierarquia.get(cat_map.get(pid), -1) >= SEPARADOR_IDX

        # varre todos os nós da hierarquia global, não só id_set
        todos_nos = set(pat_map_global.keys()) | (set(pat_map_global.values()) - {None})
        tem_separador_abaixo = {}
        for pid in sorted(todos_nos, reverse=True):
            filhos = children_map[pid]
            tem_separador_abaixo[pid] = any(
                eh_separador(f) or tem_separador_abaixo.get(f, False)
                for f in filhos
            )

        def vtp_perna(filho):
            return vtp_map.get(filho, 0) + vg_map.get(filho, 0)

        def coletar_geracao(filhos_diretos, n_geracoes):
            vtp_total = 0.0
            for filho in filhos_diretos:
                queue = deque([(filho, 1)])
                while queue:
                    node, gen = queue.popleft()
                    if gen > n_geracoes:
                        continue
                    vtp_total += vtp_map.get(node, 0)
                    for neto in children_map[node]:
                        if eh_separador(neto):
                            if neto in id_set:
                                queue.append((neto, gen + 1))
                            else:
                                queue.append((neto, gen))
                        else:
                            queue.append((neto, gen))
            return vtp_total

        df["bonus_lideranca"] = 0.0

        for pid in df["idPessoa"]:
            if cat_map.get(pid) not in bonus_lideranca_map:
                continue

            pct, n_geracoes = bonus_lideranca_map[cat_map[pid]]
            filhos_diretos = children_map[pid]

            if not filhos_diretos:
                continue

            perna_limpa = any(
                not (eh_separador(f) or tem_separador_abaixo.get(f, False))
                and vtp_perna(f) >= 1000
                for f in filhos_diretos
            )

            if not perna_limpa:
                continue

            vtp_total = coletar_geracao(filhos_diretos, n_geracoes)
            df.loc[df["idPessoa"] == pid, "bonus_lideranca"] = pct * vtp_total

        return df[["Mes", "idPessoa", "bonus_lideranca"]]


    def aplicar_por_mes(df, funcao, **kwargs):
        return pd.concat(
            (funcao(df_mes, **kwargs) for _, df_mes in df.groupby("Mes")),
            ignore_index=True
        )

    df_bonus = aplicar_por_mes(df, calcular_bonus_lideranca, pat_map_global=pat_map_global)

    df = df.drop(columns=["bonus_lideranca"], errors="ignore").merge(
        df_bonus,
        on=["Mes", "idPessoa"],
        how="left",
        validate="one_to_one"
    )


    # Bonus 7: Pool Global
    # Regra: 5% de todos os pontos serão divididos entre os top clientes proporcionais às suas cotas


    if callback_status:
        callback_status("Calculando Bônus de Pool Global... (7/7)")
    time.sleep(1)

    def calcular_bonus_global(df_mes: pd.DataFrame) -> pd.DataFrame:
        df = df_mes.copy()

        pool = df["VTP"].sum() * porcentagem_vtp_distribuido_global_pool

        df["cotas"] = df["Categoria"].map(cotas_map).fillna(0)
        total_cotas = df["cotas"].sum()

        if total_cotas == 0:
            df["bonus_global"] = 0.0
        else:
            df["bonus_global"] = df["cotas"] / total_cotas * pool

        #colunas_novas = df[["idPessoa", "bonus_global"]]
        #df_mes = df_mes.drop(columns=["bonus_global"], errors="ignore")
        #return df_mes.merge(colunas_novas, on="idPessoa", how="left")
        return df[["Mes", "idPessoa", "bonus_global"]].copy()

    # Aplicando para todos os meses
    df_bonus = aplicar_por_mes(df, calcular_bonus_global)

    df = df.drop(columns=["bonus_global"], errors="ignore").merge(
        df_bonus,
        on=["Mes", "idPessoa"],
        how="left",
        validate="one_to_one"
    )

    cols_remover = ["bonus_compra","bonus_teorico","PML_test_vg","PML_test_v3","direto"]
    df = df.drop(columns=cols_remover, errors="ignore")

    # Duplicando para bonus se tornar comissao
    colunas = ['bonus_equipe', 'bonus_producao', 'bonus_lideranca', 'bonus_global']
    df[colunas] = df[colunas] * 2

    # Somando para o bonus total de rede
    colunas = ['bonus_equipe', 'bonus_producao', 'bonus_lideranca', 'bonus_global', 'bonus_construtor']
    df['bonus_por_rede_total'] = df[colunas].sum(axis=1)

    ############################
    ############################
    ############################
    ############################
    ############################
    ############################
    ############################
    ## INÍCIOS DOS RESULTADOS ##
    ############################
    ############################
    ############################
    ############################
    ############################
    ############################

    if callback_status:
        callback_status("Calculando Resultados Finais...")


    ########################
    ## SUMARIZAÇÃO MENSAL ##
    ########################


    df_sum = df.copy()

    # -----------------------------
    # 1. Colunas de pontos
    # -----------------------------
    cols_pontos = ["pontos_cliente_prime", "pontos_compra", "pontos_recrutamento", "bonus_equipe", "bonus_producao", "bonus_construtor", "bonus_lideranca", "bonus_global", "bonus_por_rede_total"]
    df_sum[cols_pontos] = df_sum[cols_pontos] + df_sum[cols_pontos]

    # -----------------------------
    # 2. Definir agregações
    # -----------------------------
    cols_soma = [c for c in df_sum.columns if c not in [
        "Mes",
        "qtdFilhos",
        "flg_retencao",
        "VTP",
        "VG",
        "V3",
        "idPessoa",
        "idPatrocinador",
        "Categoria"]]

    agg_dict = {}

    for col in cols_soma:
        agg_dict[col] = "sum"

    # médias
    agg_dict["qtdFilhos"] = "mean"
    agg_dict["flg_retencao"] = "mean"


    # -----------------------------
    # 3. Sumarização mensal
    # -----------------------------
    df_mensal = df_sum.groupby("Mes").agg(agg_dict).reset_index()

    # -----------------------------
    # 3.b. Métricas adicionais
    # -----------------------------

    # Quantidade de novos (estagio = 0)
    novos = (
        (df_sum['estagio'] == 0)
        .groupby(df_sum['Mes'])
        .sum()
        .reset_index(name='novos')
    )

    # Receita média dos antigos (estagio != 0)
    receita_media_antigos = (
        df_sum[df_sum['estagio'] != 0]
        .groupby('Mes')['Receita']
        .mean()
        .reset_index(name='receita_media_antigos')
    )

    df_mensal = df_mensal.merge(novos, on='Mes', how='left')
    df_mensal = df_mensal.merge(receita_media_antigos, on='Mes', how='left')

    # -----------------------------
    # 4. contagem de linhas
    # -----------------------------
    df_count = df.groupby("Mes").size().reset_index(name="Consultores")

    # -----------------------------
    # 5. merge final
    # -----------------------------
    df_mensal = df_mensal.merge(df_count, on="Mes")

    # Verificando a porcentagem disso do total
    df_mensal['pct_bonus_rede'] = df_mensal['bonus_por_rede_total'] / (df_mensal['Receita_cliente'] + df_mensal['Receita'])
    df_mensal['bonus_por_receita'] = (df_mensal['bonus_por_rede_total'] + df_mensal['comissao_recrutamento']) / (df_mensal['Receita_cliente'] + df_mensal['Receita'])

    df_mensal['total_bonus'] = df_mensal['bonus_por_rede_total'] + df_mensal['comissao_recrutamento']
    df_mensal = df_mensal[['Mes', 'Consultores', 'Receita', 'Receita_cliente', 'total_bonus', 'bonus_por_receita']]

    df_mensal.columns = ['Mês', 'Consultores', 'Receita', 'Receita Cliente', 'Total Bônus', 'Bônus por Receita']



    #############################################
    ## BONUS POR CLASSIFICACAO E TIPO DE BONUS ##
    #############################################

    import numpy as np
    import pandas as pd

    df_teste_mes = df_sum[df_sum['Mes'] == meses_simulacao]

    df_teste_mes['total_bonus'] = df_teste_mes['bonus_por_rede_total'] + df_teste_mes['comissao_recrutamento']

    metricas = [
        'Receita',
        'comissao_cliente_prime',
        'comissao_recrutamento',
        'bonus_equipe',
        'bonus_producao',
        'bonus_construtor',
        'bonus_lideranca',
        'bonus_global',
        'total_bonus'
    ]

    tb_total = (
        df_teste_mes.groupby('Categoria')
        .agg(
            qtd_linhas=('Categoria', 'size'),
            **{col: (col, 'sum') for col in metricas}
        )
        .reset_index()
    )

    tb_total['Categoria'] = pd.Categorical(
        tb_total['Categoria'],
        categories=ordem_categorias,
        ordered=True
    )

    tb_total = tb_total.sort_values('Categoria').reset_index(drop=True)

    cols = ['Receita', 'comissao_cliente_prime', 'comissao_recrutamento', 'bonus_equipe', 'bonus_producao', 'bonus_construtor', 'bonus_lideranca', 'bonus_global', 'total_bonus']

    tb_total[cols] = (tb_total[cols] / 1000000).round(2) 

    linha_total = pd.DataFrame([{
        'Categoria': 'Total',
        **{
            col: tb_total[col].sum()
            for col in tb_total.columns
            if col != 'Categoria'
        }
    }]).round(2) 

    tb_total = pd.concat([tb_total, linha_total], ignore_index=True)

    tb_total.columns = ['Classificação', 'Consultores', 'Receita', 'Comissão Prime', 'Comissão Recrutamento', 'Bônus Equipe',
                         'Bônus Produção', 'Bônus Construtor', 'Bônus Liderança', 'Bônus Pool', 'Bônus Total']

    ###################################
    ## SUMARIZACAO POR CLASSIFICACAO ##
    ###################################

    tb_bonus = (
        df_teste_mes.groupby('Categoria')
        .agg(
            Consultores=('total_bonus', 'size'),
            VG_medio=('VG', 'mean'),
            Media_Bonus=('total_bonus', 'mean'),
            Mediana_Bonus=('total_bonus', 'median'),
            Maximo_Bonus=('total_bonus', 'max'),
            Minimo_Bonus=('total_bonus', 'min')
        )
        .reset_index()
    )

    tb_bonus['Categoria'] = pd.Categorical(
        tb_bonus['Categoria'],
        categories=ordem_categorias,
        ordered=True
    )

    tb_bonus = tb_bonus.sort_values('Categoria').reset_index(drop=True)

    cols = ['Consultores', 'VG_medio', 'Media_Bonus', 'Mediana_Bonus', 'Maximo_Bonus', 'Minimo_Bonus']
    tb_bonus[cols] = tb_bonus[cols].round(0).astype(int)

    tb_bonus.columns = ['Classificação', 'Consultores', 'VG Médio', 'Bônus Médio', 'Bônus Mediano', 'Bônus Mínimo', 'Bônus Máximo']

    return df_mensal, tb_total, tb_bonus