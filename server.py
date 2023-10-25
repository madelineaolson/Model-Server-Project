#!/usr/bin/env python3

import grpc
import modelserver_pb2, modelserver_pb2_grpc
import torch
import threading
from concurrent import futures

class PredictionCache:
    def __init__(self):
        self.coefs = None
        self.cache = {}
        self.evict_order = []
        self.lock = threading.Lock()
        
    def SetCoefs(self, coefs):
        with self.lock: 
            self.coefs = coefs
            self.cache = {}
            self.evict_order = []
        
    def Predict(self, X):
        with self.lock:
            bool = False
            X_rounded = torch.round(X, decimals =  4)
            X_tuple = tuple(X_rounded.flatten().tolist())     
            if X_tuple in self.cache:
                bool = True
                self.evict_order.remove(X_tuple)
                self.evict_order.append(X_tuple)
                return self.cache[X_tuple], bool

            else:
                y = X_rounded @ self.coefs
                self.cache[X_tuple] = y
                self.evict_order.append(X_tuple)

                if len(self.cache) > 10:
                    victim = self.evict_order.pop(0)
                    self.cache.pop(victim)
                return y, bool
        

class ModelServer(modelserver_pb2_grpc.ModelServerServicer):
    def __init__(self):
        self.cache = PredictionCache()
        
    def SetCoefs(self, request, context):
        coefs = torch.tensor(request.coefs)
        self.cache.SetCoefs(coefs)
        return modelserver_pb2.SetCoefsResponse(error = "")

    def Predict(self, request, context):
        X = torch.tensor(request.X)
        y, cache_bool = self.cache.Predict(X)
        response = modelserver_pb2.PredictResponse(y=y, hit=cache_bool, error="")
        return response

def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4), options=(('grpc.so_reuseport', 0),))
    modelserver_pb2_grpc.add_ModelServerServicer_to_server(ModelServer(), server)
    server.add_insecure_port("[::]:5440")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    main()
