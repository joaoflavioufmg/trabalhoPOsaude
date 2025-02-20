import pandas as pd
import plotly.express as px
import folium


class PosOtimizacao:
    def __init__(
        self,
        path_resultados,
        municipio="Contagem",
        path_demanda=None,
        path_instalacoes_primaria=None,
        path_instalacoes_sec=None,
        path_instalacoes_terc=None,
    ):
        # TODO: Criar classe builder para mestrado!
        self.formata_dfs_resultados(path=path_resultados)
        self.municipio = municipio
        if (
            path_demanda
            and path_instalacoes_primaria
            and path_instalacoes_sec
            and path_instalacoes_terc
        ):
            self.formata_dados_input(
                path_demanda,
                path_instalacoes_primaria,
                path_instalacoes_sec,
                path_instalacoes_terc,
            )

    def formata_dados_input(
        self,
        path_demanda,
        path_instalacoes_primaria,
        path_instalacoes_sec,
        path_instalacoes_terc,
    ):
        df_demanda = pd.read_excel(path_demanda)
        self.df_demanda = df_demanda[df_demanda.NM_MUN == self.municipio].reset_index(
            drop=True
        )

        n1 = pd.read_excel(path_instalacoes_primaria)
        n1 = n1[n1.municipio_nome == self.municipio.upper()].reset_index(drop=True)
        n2 = pd.read_excel(path_instalacoes_sec)
        n2 = n2[n2.municipio_nome == self.municipio.upper()].reset_index(drop=True)
        n3 = pd.read_excel(path_instalacoes_terc)
        n3 = n3[n3.municipio_nome == self.municipio.upper()].reset_index(drop=True)

        self.df_loc = pd.concat([n1, n2, n3])

    def formata_dfs_resultados(self, path):
        dfs_resultado_full = pd.read_excel(path, sheet_name=None)
        self.atr_demanda_n1 = dfs_resultado_full["Sheet1"]
        self.atr_demanda_n1["nivel"] = "Primario"
        self.atr_demanda_n1.rename(
            columns={"Ponto Demanda": "Origem", "Instalacao": "Destino"}, inplace=True
        )
        if "Valor" in self.atr_demanda_n1.columns:
            self.atr_demanda_n1.drop(columns="Valor", inplace=True)

        self.atr_n1_n2 = dfs_resultado_full["Planilha1"]
        self.atr_n1_n2["nivel"] = "Secundario"
        self.atr_n1_n2.rename(
            columns={"Origem_nivel_1": "Origem", "Destino_nivel_2": "Destino"},
            inplace=True,
        )

        self.atr_n2_n3 = dfs_resultado_full["Planilha2"]
        self.atr_n2_n3["nivel"] = "Terciario"
        self.atr_n2_n3.rename(
            columns={"Origem_nivel_2": "Origem", "Destino_nivel_3": "Destino"},
            inplace=True,
        )
        self.atribuicoes = pd.concat(
            [self.atr_demanda_n1, self.atr_n1_n2, self.atr_n2_n3]
        )

        self.abr_n1 = dfs_resultado_full["Planilha3"]
        self.abr_n1["nivel"] = "Primario"
        self.abr_n1.rename(columns={"Abertura_Nivel_1": "Abertura"}, inplace=True)
        self.abr_n2 = dfs_resultado_full["Planilha4"]
        self.abr_n2["nivel"] = "Secundario"
        self.abr_n2.rename(columns={"Abertura_Nivel_2": "Abertura"}, inplace=True)
        self.abr_n3 = dfs_resultado_full["Planilha5"]
        self.abr_n3["nivel"] = "Terciario"
        self.abr_n3.rename(columns={"Abertura_Nivel_3": "Abertura"}, inplace=True)
        self.abertura_inst = pd.concat([self.abr_n1, self.abr_n2, self.abr_n3])

        self.fluxo_eq_n1 = dfs_resultado_full["Planilha6"]
        self.fluxo_eq_n1["nivel"] = "Primario"
        self.fluxo_eq_n2 = dfs_resultado_full["Planilha7"]
        self.fluxo_eq_n2["nivel"] = "Secundario"
        self.fluxo_eq_n3 = dfs_resultado_full["Planilha8"]
        self.fluxo_eq_n3["nivel"] = "Terciario"
        self.fluxos_eq = pd.concat(
            [self.fluxo_eq_n1, self.fluxo_eq_n2, self.fluxo_eq_n3]
        )

        self.df_custos = dfs_resultado_full["Planilha9"]

    def plota_resultados_gerais(self):
        b = 0

    def plota_analises_custos(self, custos_municipio):
        def classifica_nivel(x):
            if "_n1" in x:
                return "primario"
            if "_n2" in x:
                return "secundario"
            if "_n3" in x:
                return "terciario"

        def plota_custos_modelo():
            # plota comparativo de custos do modelo!
            fig = px.bar(
                self.df_custos,
                x="Tipo_Custo",
                y="Valor",
                color="nivel",
                title="Resultados de Custo do Modelo",
            )
            fig.update_xaxes(
                showline=True,  # Mostra linhas
                showgrid=False,  # Não mostra grades
                showticklabels=True,  # Mostra rótulos
            )
            # Personalização para y-axis
            fig.update_yaxes(
                showgrid=False,  # Não mostra grade
                zeroline=False,  # Oculta a linha que representa o valor zero em y
            )

            fig.update_layout(plot_bgcolor="white")
            fig.show()

        def plota_comparativo_custos_anuais(df_custos_fim):
            fig = px.bar(
                df_custos_fim,
                x="index",
                y="Custo",
                color="nivel",
                barmode="group",
                title="Comparativo de Custos Anuais Reais",
            )
            fig.update_xaxes(
                showline=True,  # Mostra linhas
                showgrid=False,  # Não mostra grades
                showticklabels=True,  # Mostra rótulos
            )
            # Personalização para y-axis
            fig.update_yaxes(
                showgrid=False,  # Não mostra grade
                zeroline=False,  # Oculta a linha que representa o valor zero em y
            )

            fig.update_layout(plot_bgcolor="white")
            fig.show()

        df = self.df_custos.copy()
        custo_n1_modelo = (
            list(df[df.Tipo_Custo == "custo_fixo_existente_n1"]["Valor"])[0]
            + list(df[df.Tipo_Custo == "custo_fixo_novos_n1"]["Valor"])[0]
            + list(df[df.Tipo_Custo == "custo_times_novos_n1"]["Valor"])[0]
            + list(df[df.Tipo_Custo == "custo_variavel_n1"]["Valor"])[0]
        )

        custo_n2_modelo = (
            list(df[df.Tipo_Custo == "custo_fixo_existente_n2"]["Valor"])[0]
            + list(df[df.Tipo_Custo == "custo_fixo_novos_n2"]["Valor"])[0]
            + list(df[df.Tipo_Custo == "custo_times_novos_n2"]["Valor"])[0]
            + list(df[df.Tipo_Custo == "custo_variavel_n2"]["Valor"])[0]
        )

        custo_n3_modelo = (
            list(df[df.Tipo_Custo == "custo_fixo_existente_n2"]["Valor"])[0]
            + list(df[df.Tipo_Custo == "custo_fixo_novos_n2"]["Valor"])[0]
            + list(df[df.Tipo_Custo == "custo_times_novos_n2"]["Valor"])[0]
            + list(df[df.Tipo_Custo == "custo_variavel_n2"]["Valor"])[0]
        )

        custo_total_modelo = custo_n1_modelo + custo_n2_modelo + custo_n3_modelo

        self.df_custos["nivel"] = self.df_custos.Tipo_Custo.apply(
            lambda x: classifica_nivel(x)
        )

        plota_custos_modelo()
        dict_custos_modelo = {
            "custo_total": custo_total_modelo * 12,
            "custo_primario": custo_n1_modelo * 12,
            "custo_secundario_terciario": (custo_n2_modelo + custo_n3_modelo) * 12,
        }

        df_custos_modelo = (
            pd.DataFrame(data=dict_custos_modelo, index=["Custo"])
            .transpose()
            .reset_index()
        )
        df_custos_modelo["nivel"] = "Modelo"

        df_custos_reais = (
            pd.DataFrame(data=custos_municipio, index=["Custo"])
            .transpose()
            .reset_index()
        )
        df_custos_reais["nivel"] = "Real"

        df_custos_fim = pd.concat([df_custos_modelo, df_custos_reais])
        plota_comparativo_custos_anuais(df_custos_fim)
        # plota comparativo de custos do modelo!

    def plota_fluxo_equipes(self, nivel_especifico=None):
        # Fluxos por instalação
        if nivel_especifico is None:
            for lvl in pd.unique(self.fluxos_eq.nivel):
                fig = px.bar(
                    self.fluxos_eq[self.fluxos_eq.nivel == lvl],
                    x="Equipe",
                    y="Fluxo",
                    color="Instalacao",
                    title=f"Análise do Fluxo de Equipes Por Instalação do nível {lvl}",
                )

                fig.update_xaxes(
                    showline=True,  # Mostra linhas
                    showgrid=False,  # Não mostra grades
                    showticklabels=True,  # Mostra rótulos
                )
                # Personalização para y-axis
                fig.update_yaxes(
                    showgrid=False,  # Não mostra grade
                    zeroline=False,  # Oculta a linha que representa o valor zero em y
                )

                fig.update_layout(plot_bgcolor="white")
                fig.show()

                fig = px.bar(
                    self.fluxos_eq[self.fluxos_eq.nivel == lvl],
                    x="Instalacao",
                    y="Fluxo",
                    color="Equipe",
                    title=f"Análise do Fluxo de Equipes Por Equipes do nível {lvl}",
                )

                fig.update_xaxes(
                    showline=True,  # Mostra linhas
                    showgrid=False,  # Não mostra grades
                    showticklabels=True,  # Mostra rótulos
                )
                # Personalização para y-axis
                fig.update_yaxes(
                    showgrid=False,  # Não mostra grade
                    zeroline=False,  # Oculta a linha que representa o valor zero em y
                )

                fig.update_layout(plot_bgcolor="white")
                fig.show()
        else:
            lvl = nivel_especifico
            fig = px.bar(
                self.fluxos_eq[self.fluxos_eq.nivel == lvl],
                x="Equipe",
                y="Fluxo",
                color="Instalacao",
                title=f"Análise do Fluxo de Equipes Por Instalação do nível {lvl}",
            )

            fig.update_xaxes(
                showline=True,  # Mostra linhas
                showgrid=False,  # Não mostra grades
                showticklabels=True,  # Mostra rótulos
            )
            # Personalização para y-axis
            fig.update_yaxes(
                showgrid=False,  # Não mostra grade
                zeroline=False,  # Oculta a linha que representa o valor zero em y
            )

            fig.update_layout(plot_bgcolor="white")
            fig.show()

            fig = px.bar(
                self.fluxos_eq[self.fluxos_eq.nivel == lvl],
                x="Instalacao",
                y="Fluxo",
                color="Equipe",
                title=f"Análise do Fluxo de Equipes Por Equipes do nível {lvl}",
            )

            fig.update_xaxes(
                showline=True,  # Mostra linhas
                showgrid=False,  # Não mostra grades
                showticklabels=True,  # Mostra rótulos
            )
            # Personalização para y-axis
            fig.update_yaxes(
                showgrid=False,  # Não mostra grade
                zeroline=False,  # Oculta a linha que representa o valor zero em y
            )

            fig.update_layout(plot_bgcolor="white")
            fig.show()

    def plota_mapa_atribuicoes(self):
        def plota_mapas(df, nivel):
            latitude_origem = df.Latitude_Origem
            longitude_origem = df.Longitude_Origem
            m = folium.Map(
                location=[latitude_origem[0], longitude_origem[0]], zoom_start=10
            )

            latitude_destino = df.Latitude_Destino
            longitude_destino = df.Longitude_Destino
            nome_origem = df.Origem
            nome_destino = df.Destino
            valor = df.Quantidade_Pacientes_Cronicos + df.Quantidade_Pacientes_Agudos

            for i in range(len(latitude_origem)):
                folium.CircleMarker(
                    location=(latitude_origem[i], longitude_origem[i]),
                    radius=1,  # Tamanho do ponto
                    color="red",
                    fill=True,
                    fill_color="red",
                    fill_opacity=0.8,
                ).add_to(m)

                folium.CircleMarker(
                    location=(latitude_destino[i], longitude_destino[i]),
                    radius=3,
                    color="blue",
                    fill=True,
                    fill_color="blue",
                    fill_opacity=0.8,
                ).add_to(m)

                folium.PolyLine(
                    [
                        (latitude_origem[i], longitude_origem[i]),
                        (latitude_destino[i], longitude_destino[i]),
                    ],
                    color="black",
                    weight=valor[i] / 1000,
                    opacity=0.7,
                ).add_to(m)

            name = f"mapa_{nivel}.html"
            m.save(name)

        # Formatação df primário!
        df_atr = self.atribuicoes[
            self.atribuicoes["Quantidade_Pacientes_Cronicos"] > 0.1
        ]
        df_n1 = df_atr[df_atr.nivel == "Primario"].reset_index(drop=True)
        cols_n1 = ["CD_SETOR", "Total de pessoas", "Latitude", "Longitude"]
        df_n1 = df_n1.merge(
            self.df_demanda[cols_n1], right_on="CD_SETOR", left_on="Origem", how="left"
        )
        df_n1.rename(
            columns={"Latitude": "Latitude_Origem", "Longitude": "Longitude_Origem"},
            inplace=True,
        )
        cols_inst = ["nome_fantasia", "latitude", "longitude"]
        df_n1 = df_n1.merge(
            self.df_loc[cols_inst],
            right_on="nome_fantasia",
            left_on="Destino",
            how="left",
        )
        df_n1.rename(
            columns={"latitude": "Latitude_Destino", "longitude": "Longitude_Destino"},
            inplace=True,
        )

        for org in list(df_n1[df_n1.isna().any(axis=1)]["Destino"]):
            # buscando valores da coordenada nos pontos de demanda!
            CS = list(self.atr_demanda_n1["Origem"])[org]
            lat = list(self.df_demanda[self.df_demanda.CD_SETOR == CS]["Latitude"])[0]
            long = list(self.df_demanda[self.df_demanda.CD_SETOR == CS]["Longitude"])[0]
            df_n1.loc[df_n1.Destino == org, "Latitude_Destino"] = lat
            df_n1.loc[df_n1.Destino == org, "Longitude_Destino"] = long

        # Formatação secundário!
        df_n2 = df_atr[df_atr.nivel == "Secundario"].reset_index(drop=True)
        df_n2 = df_n2.merge(
            self.df_loc[cols_inst],
            right_on="nome_fantasia",
            left_on="Origem",
            how="left",
        )
        df_n2.rename(
            columns={"latitude": "Latitude_Origem", "longitude": "Longitude_Origem"},
            inplace=True,
        )

        df_n2 = df_n2.merge(
            self.df_loc[cols_inst],
            right_on="nome_fantasia",
            left_on="Destino",
            how="left",
        )
        df_n2.rename(
            columns={"latitude": "Latitude_Destino", "longitude": "Longitude_Destino"},
            inplace=True,
        )

        # Tratar Dados NAN!!
        # Se não tem coord origem n2 é porque foi ponto de demanda aberto no n1!
        # TODO: Passar para método para deixar genérico!
        for org in list(df_n2[df_n2.isna().any(axis=1)]["Origem"]):
            # buscando valores da coordenada nos pontos de demanda!
            CS = list(self.atr_demanda_n1["Origem"])[org]
            lat = list(self.df_demanda[self.df_demanda.CD_SETOR == CS]["Latitude"])[0]
            long = list(self.df_demanda[self.df_demanda.CD_SETOR == CS]["Longitude"])[0]
            df_n2.loc[df_n2.Origem == org, "Latitude_Origem"] = lat
            df_n2.loc[df_n2.Origem == org, "Longitude_Origem"] = long

        # Tratando dados terciários

        df_n3 = df_atr[df_atr.nivel == "Terciario"].reset_index(drop=True)
        df_n3 = df_n3.merge(
            self.df_loc[cols_inst],
            right_on="nome_fantasia",
            left_on="Origem",
            how="left",
        )
        df_n3.rename(
            columns={"latitude": "Latitude_Origem", "longitude": "Longitude_Origem"},
            inplace=True,
        )

        df_n3 = df_n3.merge(
            self.df_loc[cols_inst],
            right_on="nome_fantasia",
            left_on="Destino",
            how="left",
        )
        df_n3.rename(
            columns={"latitude": "Latitude_Destino", "longitude": "Longitude_Destino"},
            inplace=True,
        )

        plota_mapas(df_n1, "primario")
        plota_mapas(df_n2, "secundario")
        plota_mapas(df_n3, "terciario")

    def plota_utilizacoes_instalacoes(self):
        for lvl in pd.unique(self.atribuicoes.nivel):
            df_an = self.atribuicoes[self.atribuicoes.nivel == lvl]
            df_agg = (
                df_an.groupby(by=["Destino"])
                .agg(
                    {
                        "Quantidade_Pacientes_Cronicos": "sum",
                        "Quantidade_Pacientes_Agudos": "sum",
                    }
                )
                .reset_index()
            )
            df_agg["Total"] = (
                df_agg.Quantidade_Pacientes_Cronicos
                + df_agg.Quantidade_Pacientes_Agudos
            )

            fig = px.bar(
                df_agg,
                x="Destino",
                y="Total",
                title=f"Análise da Quantidade de Pacientes atendidos por instalações de nível {lvl}",
            )

            fig.update_xaxes(
                showline=True,  # Mostra linhas
                showgrid=False,  # Não mostra grades
                showticklabels=True,  # Mostra rótulos
            )
            # Personalização para y-axis
            fig.update_yaxes(
                showgrid=False,  # Não mostra grade
                zeroline=False,  # Oculta a linha que representa o valor zero em y
            )

            fig.update_layout(plot_bgcolor="white")
            fig.show()


if __name__ == "__main__":
    path = "resultados.xlsx"
    dados_demanda = r"C:\Users\marce\OneDrive\Área de Trabalho\trabalhoPOsaude\dados_PRONTOS_para_modelo_OTM\dados_cidades_full_MG.xlsx"
    dados_instalacoes_primarias = (
        r"dados_PRONTOS_para_modelo_OTM\instalacoes_primarias.xlsx"
    )
    dados_instalacoes_secundarias = (
        r"dados_PRONTOS_para_modelo_OTM\instalacoes_secundarias.xlsx"
    )
    dados_instalacoes_terciarias = (
        r"dados_PRONTOS_para_modelo_OTM\instalacoes_terciarias.xlsx"
    )
    municipio = "Contagem"
    pos_OTM = PosOtimizacao(
        path_resultados=path,
        path_demanda=dados_demanda,
        municipio=municipio,
        path_instalacoes_primaria=dados_instalacoes_primarias,
        path_instalacoes_sec=dados_instalacoes_secundarias,
        path_instalacoes_terc=dados_instalacoes_terciarias,
    )
    custos_contagem = {
        "custo_total": 291300000 + 142900000,
        "custo_primario": 142900000,
        "custo_secundario_terciario": 291300000,
    }

    pos_OTM.plota_mapa_atribuicoes()
    pos_OTM.plota_utilizacoes_instalacoes()
    pos_OTM.plota_fluxo_equipes()
    pos_OTM.plota_analises_custos(custos_municipio=custos_contagem)
