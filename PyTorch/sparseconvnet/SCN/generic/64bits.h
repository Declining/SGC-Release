// Copyright 2016-present, Facebook, Inc.
// All rights reserved.
//
// This source code is licensed under the license found in the
// LICENSE file in the root directory of this source tree.

#include <array>
#include <tuple>

// Using 32 bit integers for coordinates and memory calculations.
// They could be replaced with 64 bit integers.
// Advantages of 64 bit:
// - support for nFeatures * nActiveSites > 2^32 per hidden layer per batch
// Disadvantages:
// - larger, and therefore slower, data copies from CPU -> GPU
// - more device memory needed to store sparseconvnet 'rulebooks'
// - not really needed until GPUs have >> 32GB RAM

using Int = int64_t;
using uInt = uint64_t; // Max value = uInt_MAX used to denote 'non-existent'
const uInt uInt_MAX = 18446744073709551615; // 2^64-1
const uInt Int_MAX = 9223372036854775807;   // 2^63-1

// Point<dimension> is a point in the d-dimensional integer lattice
// (i.e. square-grid/cubic-grid, ...)
template <uInt dimension> using Point = std::array<Int, dimension>;

template <uInt dimension> Point<dimension> LongTensorToPoint(THLongTensor *t) {
  Point<dimension> p;
  long *td = THLongTensor_data(t);
  for (int i = 0; i < dimension; i++)
    p[i] = td[i];
  return p;
}
template <uInt dimension>
Point<2*dimension> TwoLongTensorsToPoint(THLongTensor *t0, THLongTensor *t1) {
  Point<2 * dimension> p;
  long *td;
  td = THLongTensor_data(t0);
  for (int i = 0; i < dimension; i++)
    p[i] = td[i];
  td = THLongTensor_data(t1);
  for (int i = 0; i < dimension; i++)
    p[i + dimension] = td[i];
  return p;
}
template <uInt dimension>
Point<3*dimension> ThreeLongTensorsToPoint(THLongTensor *t0, THLongTensor *t1,
                                         THLongTensor *t2) {
  Point<3 * dimension> p;
  long *td;
  td = THLongTensor_data(t0);
  for (int i = 0; i < dimension; i++)
    p[i] = td[i];
  td = THLongTensor_data(t1);
  for (int i = 0; i < dimension; i++)
    p[i + dimension] = td[i];
  td = THLongTensor_data(t2);
  for (int i = 0; i < dimension; i++)
    p[i + 2 * dimension] = td[i];
  return p;
}

// FNV Hash function for Point<dimension>
template <uInt dimension> struct IntArrayHash {
  std::size_t operator()(Point<dimension> const &p) const {
    uInt hash = 14695981039346656037;
    for (auto x : p) {
      hash *= 1099511628211;
      hash ^= x;
    }
    return hash;
  }
};

#define THCITensor THCudaLongTensor
#define THCITensor_nElement THCudaLongTensor_nElement
#define THCITensor_resize1d THCudaLongTensor_resize1d
#define THCITensor_data THCudaLongTensor_data
