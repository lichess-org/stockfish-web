#include "glue.hpp"

#include <string>

#include "evaluate.h"
#include "position.h"
#include "uci.h"
#include "nnue/nnue_architecture.h"

#if defined(STOCKFISH_WEB_FSF_14)
# include "nnue/evaluate_nnue.h"
  const std::string load_nnue_cmd(Command& cmd) {
    std::istream in(&cmd);
    if (Stockfish::Eval::NNUE::load_eval("", in))
      return "setoption name Use NNUE value true";
    else std::cerr << "BAD_NNUE" << std::endl;
    return "setoption name Use NNUE value false";
  }
#else
  extern Stockfish::UCIEngine* uci_global;

  const std::string load_nnue_cmd(Command& cmd) {
    std::istream in(&cmd);
    switch (cmd.index) {
    case 0:
      uci_global->engine.load_big_network(in);
      break;
    case 1:
# ifdef EvalFileDefaultNameSmall
      uci_global->engine.load_small_network(in);
# endif
      break;
    }
    return "";
  }
#endif

CommandQueue inQ;

extern "C" {
  EMSCRIPTEN_KEEPALIVE void uci(const char* utf8) { inQ.push(Command(utf8)); }

  EMSCRIPTEN_KEEPALIVE void setNnueBuffer(char* buf, size_t sz, int index) {
    inQ.push(Command(buf, sz, index));
  }

  EMSCRIPTEN_KEEPALIVE const char* getRecommendedNnue(int index) {
    switch (index) {
    case 0:
#if defined(EvalFileDefaultName)
      return EvalFileDefaultName;
#elif defined(EvalFileDefaultNameBig)
      return EvalFileDefaultNameBig;
#endif
      break;
    case 1:
#if defined(EvalFileDefaultNameSmall)
      return EvalFileDefaultNameSmall;
#endif
      break;
    }
    return "";
  }
}

EMSCRIPTEN_KEEPALIVE std::string js_getline() {
  auto cmd = inQ.pop();
  if (cmd.type == cmd.UCI)
    return cmd.uci;
  else if (cmd.type == cmd.NNUE && cmd.ptr)
    return load_nnue_cmd(cmd);
  else
    return "";
}
