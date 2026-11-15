import argparse

from core.brain import Brain


def conversation():
    brain = Brain()

    print("\nREDTEAM AI iniciado.")
    print("Cérebro central conectado à Groq.")

    print("""
Comandos:
/pesquisa texto
/pesquisar texto
/ler URL
/memoria
/guardar texto
/status
/limpar
/sair
""")

    while True:
        try:
            user = input("Você: ").strip()

            if not user:
                continue

            command = user.lower()

            if command in ("/sair", "sair", "exit"):
                print("REDTEAM AI encerrado.")
                break

            if command == "/limpar":
                print(brain.clear_history())
                continue

            if command == "/status":
                print(brain.status())
                continue

            if command == "/memoria":
                memories = brain.get_memories()

                if not memories:
                    print("[MEMORIA] Nenhuma memória encontrada.")
                else:
                    for item in memories:
                        print(f"[{item[0]}] {item[1]}")

                continue

            if user.startswith("/guardar "):
                content = user[len("/guardar "):].strip()

                if content:
                    print(brain.save_memory(content))

                continue

            if user.startswith(("/pesquisa ", "/pesquisar ")):
                query = user.split(" ", 1)[1].strip()

                if not query:
                    print("[ERRO] Informe o assunto.")
                    continue

                answer = brain.research(query)
                print(f"\nREDTEAM AI: {answer}\n")
                continue

            if user.startswith("/ler "):
                url = user[len("/ler "):].strip()

                if not url.startswith(("http://", "https://")):
                    print("[ERRO] URL inválida.")
                    continue

                answer = brain.read_url(url)
                print(f"\nREDTEAM AI: {answer}\n")
                continue

            answer = brain.ask(user)
            print(f"\nREDTEAM AI: {answer}\n")

        except KeyboardInterrupt:
            print("\nREDTEAM AI encerrado.")
            break

        except EOFError:
            print("\nEntrada encerrada.")
            break

        except Exception as error:
            print(f"\n[ERRO] {type(error).__name__}: {error}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        nargs="?",
        default="conversar",
        choices=["conversar", "pesquisar", "memoria"]
    )
    parser.add_argument("query", nargs="*")
    args = parser.parse_args()

    brain = Brain()

    if args.command == "conversar":
        conversation()

    elif args.command == "pesquisar":
        query = " ".join(args.query)
        if query:
            print(brain.research(query))
        else:
            print("[ERRO] Informe o assunto.")

    elif args.command == "memoria":
        for item in brain.get_memories():
            print(item)


if __name__ == "__main__":
    main()
