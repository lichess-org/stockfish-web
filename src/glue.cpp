#include "glue.hpp"

#include <string>

#include "evaluate.h"
#include "syzygy/tbprobe.h"
#include "uci.h"
#include "nnue/nnue_architecture.h"

#if __has_include("nnue/evaluate_nnue.h") // sf-16
# include "nnue/evaluate_nnue.h"
# define EvalFileDefaultNameSmall EvalFileDefaultName
# define EvalFileDefaultNameBig EvalFileDefaultName
  const std::string load_nnue_cmd(Command& cmd) {
    std::istream in(&cmd);
    if (Stockfish::Eval::NNUE::load_eval("", in))
      return "setoption name Use NNUE value true";
    else std::cerr << "BAD_NNUE" << std::endl;
    return "setoption name Use NNUE value false";
  }
#else // sf-17
  # ifndef EvalFileDefaultNameSmall // single net
  # define EvalFileDefaultNameSmall EvalFileDefaultNameBig
  # endif
  extern Stockfish::UCIEngine* uci_global;

  const std::string load_nnue_cmd(Command& cmd) {
    std::istream in(&cmd);
    if (cmd.index == 0) uci_global->engine.load_big_network(in);
    else if (cmd.index == 1) uci_global->engine.load_small_network(in);
    return "";
  }

  namespace Stockfish::Tablebases {
    // Stockfish 17
    Config rank_root_moves(const OptionsMap& o, Position& p, Search::RootMoves& rM, bool rankDTZ) {
      for (auto& m: rM) m.tbRank = 0;
      return Config();
    }
    // Stockfish 18+
    Config rank_root_moves(const OptionsMap& o, Position& p, Search::RootMoves& rM, bool rankDTZ, const std::function<bool()>& timeAbort) {
      for (auto& m: rM) m.tbRank = 0;
      return Config();
    }
  }
#endif

CommandQueue inQ;

extern "C" {
  EMSCRIPTEN_KEEPALIVE void uci(const char* utf8) { inQ.push(Command(utf8)); }

  EMSCRIPTEN_KEEPALIVE void setNnueBuffer(char* buf, size_t sz, int index) {
    inQ.push(Command(buf, sz, index));
  }

  EMSCRIPTEN_KEEPALIVE const char* getRecommendedNnue(int index) {
    return index == 1 ? EvalFileDefaultNameSmall : EvalFileDefaultNameBig;
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

namespace Stockfish::Tablebases {
  int MaxCardinality = 0;
  void init(const std::string& paths) {}
  WDLScore probe_wdl(Position& p, ProbeState* r) {
    *r = ProbeState::FAIL;
    return WDLDraw;
  }
  int probe_dtz(Position& p, ProbeState* r) {
    *r = ProbeState::FAIL;
    return 0;
  }

  bool root_probe(Position& p, Search::RootMoves& rM) { return false; }
  bool root_probe_wdl(Position& p, Search::RootMoves& rM) { return false; }
}
