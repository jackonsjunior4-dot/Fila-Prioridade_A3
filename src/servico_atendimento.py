
from paciente import Paciente


class ServicoAtendimento:

    def __init__(self, fila):
        self.fila = fila

   
    def receber_paciente(self, paciente):
        if not isinstance(paciente, Paciente):
            raise ValueError("Paciente invalido.")

        self.fila.adicionar(paciente)
        print("Paciente encaminhado para a fila:", paciente.nome)

    def chamar_proximo(self):
        paciente = self.fila.chamar()

        if paciente is not None:
            print("Chamando paciente:", paciente.nome)
            return paciente
        else:
            print("Não há pacientes aguardando.")
            return None



    
    def verificar_sla(self, paciente):
        situacao = paciente.verificar_sla()

        if situacao == "Prazo excedido":
            print("ALERTA DE SLA!")
            print("Paciente:", paciente.nome)
            return True
        else:
            print("Paciente dentro do prazo.")
            return False

   
    def verificar_alertas(self, pacientes):
        alertas = []

        for paciente in pacientes:
            if self.verificar_sla(paciente):
                alertas.append(paciente)

        return alertas



 